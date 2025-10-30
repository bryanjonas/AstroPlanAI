"""
AstroPlanAI Streamlit Web Application

A user-friendly web interface for astrophotography session planning.
"""

import streamlit as st
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from astroplanai.agents.coordinator import create_coordinator_agent
from astroplanai.config import load_config
from astroplanai.tools.ephemeris_calculator import EphemerisCalculator
from astroplanai.tools.target_database import TargetDatabase
from astropy.coordinates import EarthLocation, AltAz, SkyCoord, get_sun, get_body
import astropy.units as u


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
        st.info("Please ensure .env file is configured with VLLM_MODEL")
        st.stop()


@st.cache_resource
def get_coordinator():
    """Get coordinator agent (cached)."""
    config = load_app_config()

    coordinator = create_coordinator_agent({
        "vllm_base_url": config.vllm.base_url,
        "vllm_api_key": config.vllm.api_key,
        "vllm_model": config.vllm.model,
        "temperature": config.agent.temperature,
        "max_tokens": config.agent.max_tokens,
        "weather_api_key": config.weather_api.open_meteo_api_key,
    })

    return coordinator, config


async def run_planning(location, date_range, equipment):
    """Run the planning session asynchronously."""
    coordinator, _ = get_coordinator()

    with st.spinner("🤖 Agents are analyzing conditions..."):
        schedule = await coordinator.plan_session(location, date_range, equipment)

    return schedule


def main():
    """Main application."""

    # Header
    st.markdown('<div class="main-header">🔭 AstroPlanAI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Multi-Agent Astrophotography Planning System</div>', unsafe_allow_html=True)

    # Load config and display model info
    _, config = get_coordinator()

    st.sidebar.markdown("### System Configuration")
    st.sidebar.info(f"**Model:** {config.vllm.model}\n\n**Endpoint:** {config.vllm.base_url}")

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
                index=1,  # Default to Santa Fe
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

            st.markdown("### 📅 Date Range")

            # Date inputs
            today = datetime.now().date()
            default_start = today + timedelta(days=7)
            default_end = default_start + timedelta(days=7)

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
                value="Canon R6",
                help="Your camera model"
            )

            lens = st.text_input(
                "Lens/Telescope",
                value="400mm f/5.6",
                help="Lens or telescope description"
            )

            focal_length = st.number_input(
                "Focal Length (mm)",
                min_value=1,
                max_value=10000,
                value=400,
                step=1,
                help="Effective focal length"
            )

            sensor_width = st.number_input(
                "Sensor Width (mm)",
                min_value=1.0,
                max_value=100.0,
                value=36.0,
                step=0.1,
                help="Physical sensor width"
            )

            sensor_height = st.number_input(
                "Sensor Height (mm)",
                min_value=1.0,
                max_value=100.0,
                value=24.0,
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
            }

            # Run planning
            try:
                schedule = asyncio.run(run_planning(location, date_range, equipment))

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
            options=["Ephemeris Calculator", "Target Database Query"],
            horizontal=True
        )

        if tool_choice == "Ephemeris Calculator":
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
                    calc = EphemerisCalculator()
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

            db = TargetDatabase()

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
                    target = db.get_target_by_name(search_name)

                    if target:
                        st.success(f"Found: {target.name} - {target.common_name}")
                        st.markdown(f"""
                        - **Type:** {target.target_type.value}
                        - **Magnitude:** {target.magnitude}
                        - **Size:** {target.size_arcmin} arcmin
                        - **Coordinates:** RA {target.ra}°, Dec {target.dec}°
                        - **Best Months:** {', '.join([datetime(2000, m, 1).strftime('%b') for m in target.best_months])}
                        """)
                    else:
                        st.warning(f"Target '{search_name}' not found in database")

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
        - **Local LLM**: Powered by VLLM for privacy and control
        - **Real Data**: Uses AstroPy for calculations and Open-Meteo for weather

        ### Features

        - ✅ Real-time weather forecasts
        - ✅ Astronomical calculations (twilight, moon phase, target visibility)
        - ✅ Equipment-aware recommendations
        - ✅ Detailed imaging schedules with specific time windows
        - ✅ Dark sky location presets
        - ✅ Export plans to text files

        ### System Information

        """)

        _, config = get_coordinator()

        st.info(f"""
        **VLLM Model:** {config.vllm.model}

        **Endpoint:** {config.vllm.base_url}

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
