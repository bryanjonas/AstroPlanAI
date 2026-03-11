"""
AstroPlanAI Streamlit Web Application

A user-friendly web interface for astrophotography session planning.
"""

import streamlit as st
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
import inspect

import nest_asyncio
nest_asyncio.apply()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from astroplanai.agents.coordinator import create_coordinator_agent
from astroplanai.config import load_config
from astroplanai.tools.ephemeris_calculator import EphemerisCalculator
from astroplanai.tools.target_database import TargetDatabase
from astropy.coordinates import EarthLocation, AltAz, SkyCoord, get_sun, get_body
import astropy.units as u


def run_async(coro):
    """Run an async coroutine from sync code, compatible with Streamlit's event loop."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return loop.run_until_complete(coro)
        else:
            return asyncio.run(coro)
    except RuntimeError:
        return asyncio.run(coro)


# Page config
st.set_page_config(
    page_title="AstroPlanAI",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# Common dark sky locations
PRESET_LOCATIONS = {
    "Custom": {"lat": 0.0, "lon": 0.0, "elevation": 0},
    "Springfield, VA": {"lat": 38.7893, "lon": -77.1872, "elevation": 100},
    "Santa Fe, NM": {"lat": 35.6870, "lon": -105.9378, "elevation": 2134},
    "Cherry Springs State Park, PA": {"lat": 41.6611, "lon": -77.8206, "elevation": 664},
    "Mauna Kea, HI": {"lat": 19.8207, "lon": -155.4681, "elevation": 4207},
    "Big Bend National Park, TX": {"lat": 29.2500, "lon": -103.2500, "elevation": 1066},
    "Death Valley, CA": {"lat": 36.5054, "lon": -117.0794, "elevation": -86},
    "Jasper National Park, Canada": {"lat": 52.8734, "lon": -117.9543, "elevation": 1062},
}


def load_app_config():
    """Load configuration with error handling."""
    try:
        config = load_config()
        return config
    except Exception as e:
        st.error(f"Configuration error: {e}")
        st.info("Please ensure .env file is configured with LLM_MODEL")
        st.stop()


@st.cache_resource
def get_coordinator():
    """Get coordinator agent (cached)."""
    config = load_app_config()

    coordinator = create_coordinator_agent({
        "llm_base_url": config.llm.base_url,
        "llm_api_key": config.llm.api_key,
        "llm_model": config.llm.model,
        "temperature": config.agent.temperature,
        "max_tokens": config.agent.max_tokens,
        "weather_api_key": config.weather_api.open_meteo_api_key,
    })

    return coordinator, config


@st.cache_resource
def get_target_database():
    """Get TargetDatabase instance (cached across sessions)."""
    return TargetDatabase()


@st.cache_resource
def get_ephemeris_calculator():
    """Get EphemerisCalculator instance (cached across sessions)."""
    return EphemerisCalculator()


@st.cache_resource
def get_simbad_search():
    """Get SimbadSearch instance with persistent HTTP client (cached across sessions)."""
    from astroplanai.tools.simbad_search import SimbadSearch
    return SimbadSearch()


@st.cache_data(ttl=3600)
def cached_simbad_search(query: str):
    """Search SIMBAD with 1-hour result cache to avoid duplicate network calls."""
    simbad = get_simbad_search()
    return run_async(simbad.search_object(query))


async def run_planning(location, date_range, equipment):
    """Run the planning session asynchronously."""
    coordinator, _ = get_coordinator()

    status_container = None
    render_placeholder_fn = None
    progress_messages = []

    if hasattr(st, "status"):
        status_container = st.status(
            "🤖 Agents are analyzing conditions...",
            state="running",
            expanded=True,
        )

        def progress_callback(message: str):
            status_container.write(message)

    else:
        placeholder = st.empty()

        def render_placeholder(state: str = "info", label: str = "🤖 Agents are analyzing conditions..."):
            body_lines = [label]
            if progress_messages:
                body_lines.extend(f"- {msg}" for msg in progress_messages)
            getattr(placeholder, state)("\n".join(body_lines))

        render_placeholder_fn = render_placeholder

        def progress_callback(message: str):
            progress_messages.append(message)
            render_placeholder_fn()

        render_placeholder_fn()

    progress_callback("Initializing multi-agent workflow...")

    plan_session = coordinator.plan_session
    supports_progress = "progress_callback" in inspect.signature(plan_session).parameters

    if not supports_progress:
        progress_callback("Coordinator does not support granular updates yet; running without live steps.")

    try:
        if supports_progress:
            schedule = await plan_session(
                location, date_range, equipment, progress_callback=progress_callback
            )
        else:
            schedule = await plan_session(location, date_range, equipment)
    except Exception as e:
        if status_container is not None:
            status_container.update(label="❌ Planning failed", state="error")
            status_container.write(str(e))
        elif render_placeholder_fn:
            progress_messages.append(f"Error: {e}")
            render_placeholder_fn(state="error", label="❌ Planning failed")
        raise
    else:
        if status_container is not None:
            status_container.update(label="✅ Planning complete", state="complete")
        elif render_placeholder_fn:
            render_placeholder_fn(state="success", label="✅ Planning complete")

    return schedule


def main():
    """Main application."""

    # Header
    st.markdown('<div class="main-header">🔭 AstroPlanAI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Multi-Agent Astrophotography Planning System</div>', unsafe_allow_html=True)

    # Load config and display model info
    _, config = get_coordinator()

    st.sidebar.markdown("### System Configuration")
    st.sidebar.info(f"**Model:** {config.llm.model}\n\n**API Endpoint:** {config.llm.base_url}")

    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📅 Plan Session", "🔧 Quick Tools", "ℹ️ About"])

    # ============================================
    # TAB 1: PLAN SESSION
    # ============================================
    with tab1:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### 📍 Location")

            # Location preset
            preset = st.selectbox(
                "Quick Select",
                options=list(PRESET_LOCATIONS.keys()),
                index=1,  # Default to Springfield, VA
            )

            preset_loc = PRESET_LOCATIONS[preset]

            # Location inputs
            lat = st.number_input(
                "Latitude (degrees)",
                min_value=-90.0,
                max_value=90.0,
                value=preset_loc["lat"],
                step=0.0001,
                format="%.4f",
                help="Positive for North, negative for South"
            )

            lon = st.number_input(
                "Longitude (degrees)",
                min_value=-180.0,
                max_value=180.0,
                value=preset_loc["lon"],
                step=0.0001,
                format="%.4f",
                help="Positive for East, negative for West"
            )

            elevation = st.number_input(
                "Elevation (meters)",
                min_value=-500,
                max_value=10000,
                value=preset_loc["elevation"],
                step=1,
                help="Altitude above sea level"
            )

            st.markdown("### 🧭 Sky Coverage")

            # Sky coverage presets
            coverage_preset = st.selectbox(
                "Coverage Preset",
                options=[
                    "All Clear",
                    "North Only (Celestial Pole)",
                    "South Blocked (Trees/Building)",
                    "East & West Blocked",
                    "Custom",
                ],
                index=0,
                help="Quick presets for common obstruction patterns"
            )

            # Set defaults based on preset
            if coverage_preset == "All Clear":
                default_sectors = {"N": True, "NE": True, "E": True, "SE": True,
                                 "S": True, "SW": True, "W": True, "NW": True}
            elif coverage_preset == "North Only (Celestial Pole)":
                default_sectors = {"N": True, "NE": True, "E": False, "SE": False,
                                 "S": False, "SW": False, "W": False, "NW": True}
            elif coverage_preset == "South Blocked (Trees/Building)":
                default_sectors = {"N": True, "NE": True, "E": True, "SE": False,
                                 "S": False, "SW": False, "W": True, "NW": True}
            elif coverage_preset == "East & West Blocked":
                default_sectors = {"N": True, "NE": False, "E": False, "SE": False,
                                 "S": True, "SW": False, "W": False, "NW": False}
            else:  # Custom
                default_sectors = {"N": True, "NE": True, "E": True, "SE": True,
                                 "S": True, "SW": True, "W": True, "NW": True}

            st.markdown("Select which sky sectors are **clear** for imaging (unchecked = obstructed):")

            # Create 8-sector compass selector with styling
            st.markdown("""
            <style>
            .compass-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 5px;
                max-width: 250px;
                margin: 10px auto;
            }
            </style>
            """, unsafe_allow_html=True)

            # Create 8-sector compass selector
            col_nw, col_n, col_ne = st.columns(3)
            col_w, col_center, col_e = st.columns(3)
            col_sw, col_s, col_se = st.columns(3)

            with col_nw:
                nw = st.checkbox("↖ NW", value=default_sectors["NW"], key="nw", help="Northwest (315°)")
            with col_n:
                n = st.checkbox("↑ N", value=default_sectors["N"], key="n", help="North (0°)")
            with col_ne:
                ne = st.checkbox("↗ NE", value=default_sectors["NE"], key="ne", help="Northeast (45°)")
            with col_w:
                w = st.checkbox("← W", value=default_sectors["W"], key="w", help="West (270°)")
            with col_center:
                st.markdown("<div style='text-align: center; padding: 10px; font-size: 24px;'>🔭</div>", unsafe_allow_html=True)
            with col_e:
                e = st.checkbox("→ E", value=default_sectors["E"], key="e", help="East (90°)")
            with col_sw:
                sw = st.checkbox("↙ SW", value=default_sectors["SW"], key="sw", help="Southwest (225°)")
            with col_s:
                s = st.checkbox("↓ S", value=default_sectors["S"], key="s", help="South (180°)")
            with col_se:
                se = st.checkbox("↘ SE", value=default_sectors["SE"], key="se", help="Southeast (135°)")

            # Build list of available sectors
            available_sectors = []
            if n: available_sectors.append("N")
            if ne: available_sectors.append("NE")
            if e: available_sectors.append("E")
            if se: available_sectors.append("SE")
            if s: available_sectors.append("S")
            if sw: available_sectors.append("SW")
            if w: available_sectors.append("W")
            if nw: available_sectors.append("NW")

            if len(available_sectors) == 0:
                st.error("⚠️ No sky sectors selected. Please select at least one clear direction.")
            elif len(available_sectors) < 4:
                st.info(f"🔭 **Limited Coverage**: {len(available_sectors)}/8 sectors clear ({', '.join(available_sectors)})")
                st.caption("Targets will be filtered to available sectors only")
            else:
                st.success(f"✅ **Sky Coverage**: {len(available_sectors)}/8 sectors clear ({', '.join(available_sectors)})")

            # Minimum altitude constraint
            min_altitude = st.slider(
                "Minimum Target Altitude (degrees above horizon)",
                min_value=0,
                max_value=60,
                value=30,
                step=5,
                help="Ignore targets below this altitude (accounts for trees, buildings, atmospheric extinction)"
            )

            st.markdown("### 📅 Date Range")

            # Date inputs
            today = datetime.now().date()
            default_start = today #+ timedelta(days=7)
            default_end = default_start + timedelta(days=3)

            start_date = st.date_input(
                "Start Date",
                value=default_start,
                min_value=today,
                help="First night to analyze"
            )

            end_date = st.date_input(
                "End Date",
                value=default_end,
                min_value=start_date,
                help="Last night to analyze"
            )

            # Validate date range
            if (end_date - start_date).days > 30:
                st.warning("⚠️ Date ranges longer than 30 days may take significant time to process.")

        with col2:
            st.markdown("### 🔭 Equipment")

            camera = st.text_input(
                "Camera",
                value="ASI585MC PRO",
                help="Your camera model"
            )

            lens = st.text_input(
                "Lens/Telescope",
                value="RedCat 51 (250mm f/4.9)",
                help="Lens or telescope description"
            )

            focal_length = st.number_input(
                "Focal Length (mm)",
                min_value=1,
                max_value=10000,
                value=250,
                step=1,
                help="Effective focal length"
            )

            sensor_width = st.number_input(
                "Sensor Width (mm)",
                min_value=1.0,
                max_value=100.0,
                value=8.4,
                step=0.1,
                help="Physical sensor width"
            )

            sensor_height = st.number_input(
                "Sensor Height (mm)",
                min_value=1.0,
                max_value=100.0,
                value=7.1,
                step=0.1,
                help="Physical sensor height"
            )

            mount = st.selectbox(
                "Mount Type",
                options=[
                    "Equatorial with tracking",
                    "Alt-azimuth with tracking",
                    "Fixed tripod (no tracking)",
                    "Star tracker",
                ],
                index=0,  # Default to Star tracker
                help="Mount and tracking capabilities"
            )

        st.markdown("---")

        # Generate button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            generate_button = st.button(
                "🚀 Generate Imaging Plan",
                type="primary",
                use_container_width=True
            )

        # Process planning request
        if generate_button:
            # Prepare inputs
            location = {
                "lat": lat,
                "lon": lon,
                "elevation": elevation,
            }

            date_range = {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            }

            equipment = {
                "camera": camera,
                "lens": lens,
                "focal_length_mm": focal_length,
                "sensor_width_mm": sensor_width,
                "sensor_height_mm": sensor_height,
                "mount": mount,
                "sky_coverage": {
                    "available_sectors": available_sectors,
                    "min_altitude_deg": min_altitude,
                },
            }

            # Run planning
            try:
                schedule = run_async(run_planning(location, date_range, equipment))

                st.markdown("---")
                st.markdown("### 📋 Imaging Plan")

                # Display results
                st.success("✅ Plan generated successfully!")
                st.markdown(schedule)

                # Export option
                st.download_button(
                    label="📥 Download Plan as Text",
                    data=schedule,
                    file_name=f"astroplan_{start_date}_{end_date}.txt",
                    mime="text/plain",
                )

            except Exception as e:
                error_msg = str(e)

                # Check for specific error types
                if "max_tokens must be at least 1" in error_msg or "max_tokens" in error_msg and "BadRequestError" in str(type(e).__name__):
                    st.error("❌ **Context Length Exceeded**")
                    st.warning("""
                    The combined prompt is too long for your model's context window.

                    **Solutions:**
                    1. **Reduce date range**: Try a shorter period (3-5 days instead of 7+)
                    2. **Lower AGENT_MAX_TOKENS**: Set to 1024 or 1536 in your `.env` file
                    3. **Use a larger model**: Switch to a model with bigger context window
                    4. **Restart container**: If you changed `.env`, restart with `docker-compose restart webapp`

                    Current settings can be viewed in the sidebar.
                    """)
                else:
                    st.error(f"❌ Error generating plan: {e}")

                with st.expander("View full error details"):
                    st.exception(e)

    # ============================================
    # TAB 2: QUICK TOOLS
    # ============================================
    with tab2:
        st.markdown("### 🔧 Astronomy Tools")

        tool_choice = st.radio(
            "Select Tool",
            options=["AI Target Search", "Ephemeris Calculator", "Target Database Query"],
            horizontal=True
        )

        if tool_choice == "AI Target Search":
            st.markdown("#### AI-Powered Target Search")
            st.caption("Search millions of astronomical objects using SIMBAD database + AI recommendations")

            search_query = st.text_input(
                "What would you like to image?",
                placeholder="e.g., 'M33', 'bright galaxies in autumn', 'nebulae for 250mm scope'",
                help="Natural language search or specific object name"
            )

            col1, col2 = st.columns(2)
            with col1:
                search_focal_length = st.number_input(
                    "Your Focal Length (mm)",
                    min_value=1,
                    max_value=10000,
                    value=250,
                    help="For field of view calculations"
                )
            with col2:
                search_sensor_width = st.number_input(
                    "Sensor Width (mm)",
                    min_value=1.0,
                    max_value=100.0,
                    value=8.4,
                    help="For field of view calculations"
                )

            if st.button("🔍 Search", key="ai_search"):
                if not search_query:
                    st.warning("Please enter a search query")
                else:
                    with st.spinner("Searching astronomical databases..."):
                        try:
                            # Search SIMBAD (results cached for 1 hour)
                            simbad_result = cached_simbad_search(search_query)

                            if simbad_result:
                                st.success(f"✅ Found in SIMBAD: {simbad_result['name']}")

                                col1, col2 = st.columns(2)

                                with col1:
                                    st.markdown("**Object Information**")
                                    st.write(f"**Name:** {simbad_result['name']}")
                                    st.write(f"**Type:** {simbad_result['object_type']}")
                                    if simbad_result.get('magnitude'):
                                        st.write(f"**Magnitude:** {simbad_result['magnitude']:.1f}")
                                    if simbad_result.get('size_arcmin'):
                                        st.write(f"**Size:** {simbad_result['size_arcmin']:.1f} arcmin")

                                with col2:
                                    st.markdown("**Coordinates**")
                                    if simbad_result.get('ra') and simbad_result.get('dec'):
                                        st.write(f"**RA:** {simbad_result['ra']:.4f}°")
                                        st.write(f"**Dec:** {simbad_result['dec']:.4f}°")

                                        # Calculate field of view
                                        sensor_diag = (search_sensor_width**2 + (search_sensor_width*0.75)**2)**0.5
                                        fov_deg = 2 * (180/3.14159) * (sensor_diag / (2*search_focal_length)) * 57.3
                                        fov_arcmin = fov_deg * 60

                                        st.markdown("**Field of View Match**")
                                        if simbad_result.get('size_arcmin'):
                                            obj_size = simbad_result['size_arcmin']
                                            if obj_size < fov_arcmin * 0.2:
                                                st.info(f"🔭 Object is small ({obj_size:.1f}') compared to your FOV ({fov_arcmin:.1f}'). Consider higher magnification.")
                                            elif obj_size > fov_arcmin * 1.5:
                                                st.warning(f"⚠️ Object ({obj_size:.1f}') is larger than your FOV ({fov_arcmin:.1f}'). You'll capture only part of it.")
                                            else:
                                                st.success(f"✅ Good fit! Object ({obj_size:.1f}') fits well in your FOV ({fov_arcmin:.1f}').")

                                # Now get AI recommendations
                                st.markdown("---")
                                st.markdown("**AI Imaging Recommendations**")

                                with st.spinner("Getting AI recommendations..."):
                                    from astroplanai.agents.target_search import create_target_search_agent

                                    coordinator, config = get_coordinator()
                                    client = coordinator.client

                                    search_agent = create_target_search_agent(
                                        client,
                                        config.llm.model,
                                        temperature=0.7,
                                        max_tokens=1024,
                                    )

                                    equipment_context = f"""
Object: {simbad_result['name']} ({simbad_result['object_type']})
Magnitude: {simbad_result.get('magnitude', 'unknown')}
Size: {simbad_result.get('size_arcmin', 'unknown')} arcmin
Your Equipment: {search_focal_length}mm focal length, {search_sensor_width}mm sensor
Your FOV: {fov_arcmin:.1f} arcmin
"""

                                    prompt = f"""Provide imaging recommendations for this target:

{equipment_context}

Include:
1. Imaging difficulty (easy/moderate/challenging) and why
2. Recommended exposure time and ISO/gain settings
3. Best filters to use (if any)
4. Composition tips for this target
5. Common challenges when imaging this object

Keep it concise and practical."""

                                    recommendations = run_async(search_agent.generate(prompt))
                                    st.markdown(recommendations)

                            else:
                                # Object not found in SIMBAD, use AI to help
                                st.info("💡 Object not found in SIMBAD. Using AI to help with your query...")

                                from astroplanai.agents.target_search import create_target_search_agent

                                coordinator, config = get_coordinator()
                                client = coordinator.client

                                search_agent = create_target_search_agent(
                                    client,
                                    config.llm.model,
                                    temperature=0.7,
                                    max_tokens=1024,
                                )

                                prompt = f"""Help find astronomical targets matching this query: "{search_query}"

Equipment: {search_focal_length}mm focal length, {search_sensor_width}mm sensor width

Suggest 3-5 suitable targets with:
1. Object name and type
2. Approximate coordinates
3. Brightness and size
4. Why it matches the query
5. Imaging difficulty

Be specific and practical."""

                                recommendations = run_async(search_agent.generate(prompt))
                                st.markdown(recommendations)

                        except Exception as e:
                            st.error(f"Search error: {e}")
                            with st.expander("View error details"):
                                st.exception(e)

        elif tool_choice == "Ephemeris Calculator":
            st.markdown("#### Calculate astronomical events for a specific night")

            col1, col2 = st.columns(2)

            with col1:
                calc_lat = st.number_input("Latitude", value=35.6870, format="%.4f", key="calc_lat")
                calc_lon = st.number_input("Longitude", value=-105.9378, format="%.4f", key="calc_lon")
                calc_elev = st.number_input("Elevation (m)", value=2134, key="calc_elev")

            with col2:
                calc_date = st.date_input("Date", value=datetime.now().date(), key="calc_date")

            if st.button("Calculate", key="calc_button"):
                try:
                    calc = get_ephemeris_calculator()
                    location = EarthLocation(
                        lat=calc_lat * u.deg,
                        lon=calc_lon * u.deg,
                        height=calc_elev * u.m
                    )

                    # Convert date to datetime
                    calc_datetime = datetime.combine(calc_date, datetime.min.time())

                    with st.spinner("Calculating..."):
                        twilight = calc.calculate_astronomical_twilight(location, calc_datetime)
                        moon_info = calc.calculate_moon_info(location, calc_datetime)

                    st.success("Calculations complete!")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**Twilight Times**")
                        st.json(twilight)

                    with col2:
                        st.markdown("**Moon Information**")
                        st.json(moon_info)

                except Exception as e:
                    st.error(f"Error: {e}")

        else:  # Target Database Query
            st.markdown("#### Search for deep-sky objects")

            db = get_target_database()

            query_type = st.radio(
                "Query Type",
                options=["By Season", "By Name", "By Type"],
                horizontal=True
            )

            if query_type == "By Season":
                month = st.selectbox(
                    "Month",
                    options=list(range(1, 13)),
                    format_func=lambda x: datetime(2000, x, 1).strftime("%B")
                )

                if st.button("Search", key="season_search"):
                    targets = db.filter_by_season(month)

                    st.markdown(f"**Found {len(targets)} targets visible in {datetime(2000, month, 1).strftime('%B')}**")

                    for target in targets[:20]:  # Limit to 20
                        with st.expander(f"{target.name} - {target.common_name}"):
                            st.markdown(f"""
                            - **Type:** {target.target_type.value}
                            - **Magnitude:** {target.magnitude}
                            - **Size:** {target.size_arcmin} arcmin
                            - **Coordinates:** RA {target.ra}°, Dec {target.dec}°
                            - **Best Months:** {', '.join([datetime(2000, m, 1).strftime('%b') for m in target.best_months])}
                            """)

            elif query_type == "By Name":
                search_name = st.text_input("Target Name (e.g., M31, NGC 7000)")

                if st.button("Search", key="name_search"):
                    targets = db.search_by_name(search_name)

                    if targets:
                        st.success(f"Found {len(targets)} matching target(s)")
                        for target in targets:
                            with st.expander(f"{target.name} - {target.common_name}"):
                                st.markdown(f"""
                                - **Type:** {target.target_type.value}
                                - **Magnitude:** {target.magnitude}
                                - **Size:** {target.size_arcmin} arcmin
                                - **Coordinates:** RA {target.ra}°, Dec {target.dec}°
                                - **Best Months:** {', '.join([datetime(2000, m, 1).strftime('%b') for m in target.best_months])}
                                """)
                    else:
                        st.warning(f"No targets found matching '{search_name}'")

            else:  # By Type
                from astroplanai.tools.target_database import TargetType

                target_type = st.selectbox(
                    "Target Type",
                    options=[t.value for t in TargetType]
                )

                if st.button("Search", key="type_search"):
                    type_enum = TargetType(target_type)
                    targets = db.filter_by_type(type_enum)

                    st.markdown(f"**Found {len(targets)} {target_type} targets**")

                    for target in targets[:20]:
                        with st.expander(f"{target.name} - {target.common_name}"):
                            st.markdown(f"""
                            - **Magnitude:** {target.magnitude}
                            - **Size:** {target.size_arcmin} arcmin
                            - **Coordinates:** RA {target.ra}°, Dec {target.dec}°
                            - **Best Months:** {', '.join([datetime(2000, m, 1).strftime('%b') for m in target.best_months])}
                            """)

    # ============================================
    # TAB 3: ABOUT
    # ============================================
    with tab3:
        st.markdown("""
        ## About AstroPlanAI

        AstroPlanAI is a multi-agent system that helps astrophotographers plan optimal imaging sessions.

        ### How It Works

        The system uses specialized AI agents that work together:

        1. **Weather Agent** - Analyzes atmospheric conditions and forecasts
        2. **Ephemeris Agent** - Calculates celestial mechanics (moon phase, twilight times, etc.)
        3. **Target Selection Agent** - Recommends deep-sky objects based on conditions
        4. **Scheduler Agent** - Synthesizes all data into an actionable imaging plan

        ### Architecture

        - **Multi-Agent Orchestration**: Parallel processing of weather, ephemeris, and target data
        - **Local or Remote LLM**: Works with any OpenAI-compatible API endpoint
        - **Real Data**: Uses AstroPy for calculations and Open-Meteo for weather

        ### Features

        - ✅ **AI Target Search** - Search millions of objects via SIMBAD + get AI imaging recommendations
        - ✅ Real-time weather forecasts
        - ✅ Astronomical calculations (twilight, moon phase, target visibility)
        - ✅ Equipment-aware recommendations with field-of-view matching
        - ✅ **Sky Coverage Constraints** - Account for obstructions (trees, buildings) by sector
        - ✅ **Altitude Filtering** - Set minimum altitude to avoid atmospheric extinction
        - ✅ Detailed imaging schedules with specific time windows
        - ✅ Dark sky location presets
        - ✅ Export plans to text files

        ### System Information

        """)

        _, config = get_coordinator()

        st.info(f"""
        **Model:** {config.llm.model}

        **API Endpoint:** {config.llm.base_url}

        **Temperature:** {config.agent.temperature}

        **Max Tokens:** {config.agent.max_tokens}
        """)

        st.markdown("""
        ### Data Sources

        - **Weather**: [Open-Meteo API](https://open-meteo.com/)
        - **Ephemeris**: [AstroPy](https://www.astropy.org/)
        - **Targets**: Curated database of Messier, NGC, and IC objects

        ### Getting Help

        For documentation and support, see the project repository.
        """)


if __name__ == "__main__":
    main()
