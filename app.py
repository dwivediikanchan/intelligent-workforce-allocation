
import importlib
import traceback
from pathlib import Path

import streamlit as st


# =========================================================
# 1. APPLICATION CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Tech Mahindra | Workforce Allocation",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "assets" / "tech_mahindra_logo.png"


# =========================================================
# 2. GLOBAL CORPORATE THEME
# =========================================================

st.markdown(
    """
    <style>

    :root {
        --tm-red: #E31837;
        --tm-red-light: #FFF0F2;
        --tm-navy: #17144A;
        --tm-grey: #55565A;
        --tm-light: #F5F6F8;
        --tm-white: #FFFFFF;
        --tm-border: #DADCE2;
    }

    /* MAIN APPLICATION */

    .stApp {
        background: #F5F6F8 !important;
        color: #292929 !important;
    }

    [data-testid="stHeader"] {
        background: #FFFFFF !important;
    }

    [data-testid="stMain"] {
        background: #F5F6F8 !important;
    }

    .main .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1500px !important;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #17144A !important;
    }

    p, li, label {
        color: #333333;
    }

    /* SIDEBAR */

    [data-testid="stSidebar"] {
        background: #FFFFFF !important;
        border-right: 1px solid #DADCE2 !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        background: #FFFFFF !important;
        padding-top: 1rem !important;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #17144A !important;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #17144A !important;
    }

    [data-testid="stSidebar"] .stRadio > div {
        gap: 7px !important;
    }

    [data-testid="stSidebar"] .stRadio label {
        background: #F5F6F8 !important;
        border: 1px solid #E2E3E8 !important;
        border-radius: 8px !important;
        padding: 9px 12px !important;
        margin-bottom: 3px !important;
        color: #17144A !important;
        cursor: pointer !important;
        transition: all 0.2s ease-in-out;
    }

    [data-testid="stSidebar"] .stRadio label p,
    [data-testid="stSidebar"] .stRadio label span,
    [data-testid="stSidebar"] .stRadio label div {
        color: #17144A !important;
        opacity: 1 !important;
    }

    [data-testid="stSidebar"] .stRadio label:hover {
        background: #FFF0F2 !important;
        border-color: #E31837 !important;
    }

    [data-testid="stSidebar"] .stRadio label:has(input:checked) {
        background: #E31837 !important;
        border-color: #E31837 !important;
    }

    [data-testid="stSidebar"] .stRadio label:has(input:checked) p,
    [data-testid="stSidebar"] .stRadio label:has(input:checked) span,
    [data-testid="stSidebar"] .stRadio label:has(input:checked) div {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    /* BUTTONS */

    .stButton button,
    .stDownloadButton button,
    [data-testid="stFormSubmitButton"] button,
    [data-testid="stPopover"] button {
        background: #E31837 !important;
        color: #FFFFFF !important;
        border: 1px solid #E31837 !important;
        border-radius: 7px !important;
        font-weight: 650 !important;
        opacity: 1 !important;
        visibility: visible !important;
        transition: all 0.2s ease-in-out !important;
    }

    .stButton button *,
    .stDownloadButton button *,
    [data-testid="stFormSubmitButton"] button *,
    [data-testid="stPopover"] button * {
        color: #FFFFFF !important;
        opacity: 1 !important;
        visibility: visible !important;
    }

    .stButton button:hover,
    .stDownloadButton button:hover,
    [data-testid="stFormSubmitButton"] button:hover,
    [data-testid="stPopover"] button:hover {
        background: #17144A !important;
        border-color: #17144A !important;
        color: #FFFFFF !important;
    }

    button:disabled {
        opacity: 0.65 !important;
        cursor: not-allowed !important;
    }

    /* INPUTS */

    input,
    textarea,
    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea {
        background: #FFFFFF !important;
        color: #222222 !important;
        border-color: #BFC2CA !important;
        opacity: 1 !important;
    }

    input::placeholder,
    textarea::placeholder {
        color: #777777 !important;
        opacity: 1 !important;
    }

    [data-testid="stTextInput"] label,
    [data-testid="stTextArea"] label,
    [data-testid="stNumberInput"] label,
    [data-testid="stDateInput"] label,
    [data-testid="stTimeInput"] label {
        color: #17144A !important;
        font-weight: 600 !important;
    }

    /* SELECT BOXES */

    [data-baseweb="select"] > div {
        background: #FFFFFF !important;
        border-color: #BFC2CA !important;
        color: #222222 !important;
    }

    [data-baseweb="select"] *,
    [data-baseweb="select"] input {
        color: #222222 !important;
        opacity: 1 !important;
    }

    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [role="listbox"] {
        background: #FFFFFF !important;
        color: #222222 !important;
    }

    [role="option"] {
        background: #FFFFFF !important;
        color: #222222 !important;
    }

    [role="option"]:hover,
    [role="option"][aria-selected="true"] {
        background: #FFF0F2 !important;
        color: #17144A !important;
    }

    /* CHECKBOXES AND RADIO */

    [data-testid="stCheckbox"] label,
    [data-testid="stRadio"] label,
    [data-testid="stToggle"] label {
        color: #17144A !important;
        opacity: 1 !important;
    }

    [data-testid="stCheckbox"] label p,
    [data-testid="stRadio"] label p {
        color: #17144A !important;
        opacity: 1 !important;
    }

    /* TABS */

    [data-testid="stTabs"] button {
        color: #17144A !important;
        font-weight: 650 !important;
        opacity: 1 !important;
    }

    [data-testid="stTabs"] button:hover {
        color: #E31837 !important;
        background: #FFF0F2 !important;
    }

    [data-testid="stTabs"] button[aria-selected="true"] {
        color: #E31837 !important;
        border-bottom: 3px solid #E31837 !important;
    }

    /* EXPANDERS */

    [data-testid="stExpander"] {
        background: #FFFFFF !important;
        border: 1px solid #DADCE2 !important;
        border-radius: 9px !important;
    }

    [data-testid="stExpander"] summary {
        color: #17144A !important;
        font-weight: 650 !important;
    }

    [data-testid="stExpander"] summary p {
        color: #17144A !important;
    }

    /* TABLES */

    [data-testid="stDataFrame"],
    [data-testid="stTable"] {
        background: #FFFFFF !important;
        border: 1px solid #DADCE2 !important;
        border-radius: 8px !important;
    }

    /* GENERAL CONTAINERS */

    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #FFFFFF !important;
        border: 1px solid #DADCE2 !important;
        border-radius: 10px !important;
    }

    /* FILE UPLOADER */

    [data-testid="stFileUploader"] {
        background: #FFFFFF !important;
        border: 1px dashed #AEB2BC !important;
        border-radius: 9px !important;
        padding: 10px !important;
    }

    [data-testid="stFileUploader"] label,
    [data-testid="stFileUploader"] p,
    [data-testid="stFileUploader"] span {
        color: #17144A !important;
        opacity: 1 !important;
    }

    /* ALERTS */

    [data-testid="stAlert"] {
        border-radius: 8px !important;
        opacity: 1 !important;
    }

    /* FOOTER */

    footer {
        visibility: hidden;
    }

    /* =================================================
       COMMON CARD DESIGN
    ================================================= */

    .capability-card {
        background: #FFFFFF !important;
        border: 1px solid #DADCE2 !important;
        border-top: 4px solid #E31837 !important;
        border-radius: 12px !important;
        padding: 20px 18px !important;
        min-height: 155px !important;
        height: 100% !important;
        box-shadow: 0 3px 10px rgba(23, 20, 74, 0.06) !important;
        transition: all 0.2s ease-in-out;
        box-sizing: border-box;
    }

    .capability-card:hover {
        border-color: #E31837 !important;
        box-shadow: 0 6px 16px rgba(23, 20, 74, 0.12) !important;
        transform: translateY(-3px);
    }

    .capability-card h4 {
        color: #17144A !important;
        font-size: 17px !important;
        font-weight: 700 !important;
        margin: 0 0 12px 0 !important;
        line-height: 1.4 !important;
    }

    .capability-card p {
        color: #55565A !important;
        font-size: 14px !important;
        line-height: 1.65 !important;
        margin: 0 !important;
    }

    .capability-section-title {
        color: #17144A !important;
        font-size: 25px !important;
        font-weight: 750 !important;
        margin-bottom: 20px !important;
    }

    /* =================================================
       WORKFORCE AND QUALITY METRIC CARDS
    ================================================= */

    .metric-card {
        min-height: 145px !important;
        height: 145px !important;
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 20px !important;
        box-sizing: border-box;
    }

    .metric-card-label {
        color: #55565A !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        margin: 0 0 8px 0 !important;
    }

    .metric-card-value {
        color: #17144A !important;
        font-size: 32px !important;
        font-weight: 750 !important;
        margin: 0 0 7px 0 !important;
        line-height: 1.2 !important;
    }

    .metric-card-caption {
        color: #777777 !important;
        font-size: 12px !important;
        margin: 0 !important;
    }

    @media (max-width: 768px) {

        .capability-card {
            min-height: 130px !important;
        }

        .metric-card {
            min-height: 125px !important;
            height: 125px !important;
        }

        .metric-card-value {
            font-size: 27px !important;
        }

    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 3. SIDEBAR NAVIGATION
# =========================================================

PAGES = [
    "Home",
    "Employee Management",
    "Attendance Management",
    "Smart Allocation",
    "Manager Dashboard",
    "Workforce Analytics",
    "Skill Gap Analysis",
    "Quality Intelligence",
    "Allocation History",
    "Workforce Data Upload"
]

with st.sidebar:

    st.caption("TECH MAHINDRA")

    st.title("WORKFORCE OS")

    st.caption("Intelligent Workforce Management")

    st.divider()

    st.markdown("### MAIN MENU")

    selected_page = st.radio(
        "Navigation",
        PAGES,
        index=0,
        label_visibility="collapsed",
        key="main_navigation"
    )

    st.divider()

    st.caption("TECH MAHINDRA")
    st.caption("Workforce Intelligence Platform")
    st.caption("Python | PostgreSQL | Streamlit")
    st.caption("© 2026")


# =========================================================
# 4. MAIN HEADER
# =========================================================

with st.container(border=True):

    logo_col, title_col = st.columns(
        [1.3, 5],
        vertical_alignment="center"
    )

    with logo_col:

        if LOGO_PATH.exists():

            st.image(
                str(LOGO_PATH),
                width=180
            )

        else:

            st.subheader("TECH MAHINDRA")
            st.caption("Logo file not found")

    with title_col:

        st.title("Workforce Operations Platform")

        st.caption(
            "Intelligent workforce management | "
            "Skill-based allocation | "
            "Attendance monitoring | "
            "Manufacturing quality intelligence"
        )

st.divider()


# =========================================================
# 5. HELPER FUNCTIONS
# =========================================================

def safe_row_count(dataframe):

    if dataframe is None:
        return 0

    try:
        return len(dataframe)

    except TypeError:
        return 0


# =========================================================
# 6. REUSABLE HTML CARD FUNCTION
# =========================================================

def show_metric_card(label, value, description):

    st.markdown(
        f"""
        <div class="capability-card metric-card">
            <p class="metric-card-label">{label}</p>
            <h2 class="metric-card-value">{value:,}</h2>
            <p class="metric-card-caption">{description}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# 7. PLATFORM CAPABILITIES
# =========================================================

def show_platform_capabilities():

    st.markdown(
        '<div class="capability-section-title">'
        'Platform Capabilities'
        '</div>',
        unsafe_allow_html=True
    )

    capabilities = [
        (
            "Employee Management",
            "Register employees, manage skills and verify employee competencies."
        ),
        (
            "Manager Dashboard",
            "Manage assignments, approve station changes and track audit history."
        ),
        (
            "Quality Intelligence",
            "Analyze manufacturing defects and station-level quality performance."
        ),
        (
            "Attendance Management",
            "Record, update and validate daily workforce attendance."
        ),
        (
            "Workforce Analytics",
            "Analyze workforce availability, station eligibility and capacity."
        ),
        (
            "Allocation History",
            "Track historical allocation changes and manager activities."
        ),
        (
            "Smart Allocation",
            "Generate skill-based station recommendations and validate capacity."
        ),
        (
            "Skill Gap Analysis",
            "Identify missing competencies and employee training requirements."
        ),
        (
            "Workforce Data Upload",
            "Upload workforce datasets, validate records and generate recommendations."
        )
    ]

    for row_start in range(0, len(capabilities), 3):

        columns = st.columns(3, gap="medium")

        for col_index, column in enumerate(columns):

            item_index = row_start + col_index

            if item_index >= len(capabilities):
                continue

            heading, description = capabilities[item_index]

            with column:

                st.markdown(
                    f"""
                    <div class="capability-card">
                        <h4>{heading}</h4>
                        <p>{description}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    st.write("")


# =========================================================
# 8. HOME DASHBOARD
# =========================================================

def show_home_dashboard():

    st.header("Workforce Operations Overview")

    st.write(
        "A centralized platform for intelligent workforce "
        "management, skill-based allocation, attendance monitoring "
        "and manufacturing quality intelligence."
    )

    try:

        from database_repository import (
            get_employees,
            get_employee_skills,
            get_stations,
            get_station_requirements,
            get_attendance,
            get_allocations,
            get_allocation_audit,
            get_defect_records
        )

        employees = get_employees()
        skills = get_employee_skills()
        stations = get_stations()
        requirements = get_station_requirements()
        attendance = get_attendance()
        allocations = get_allocations()
        audit = get_allocation_audit()
        defects = get_defect_records()

        total_employees = safe_row_count(employees)
        total_skills = safe_row_count(skills)
        total_stations = safe_row_count(stations)
        total_attendance = safe_row_count(attendance)
        total_allocations = safe_row_count(allocations)
        total_requirements = safe_row_count(requirements)
        total_audit = safe_row_count(audit)
        total_defects = safe_row_count(defects)

        active_employees = total_employees

        if employees is not None and not employees.empty:

            if "status" in employees.columns:

                active_employees = int(
                    employees["status"]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                    .isin(["active", "available"])
                    .sum()
                )

        st.success(
            "PostgreSQL database connection successful."
        )

        # =================================================
        # WORKFORCE SUMMARY
        # =================================================

        st.divider()

        st.subheader("Workforce Summary")

        workforce_metrics = [
            ("Total Employees", total_employees),
            ("Active Employees", active_employees),
            ("Employee Skills", total_skills),
            ("Production Stations", total_stations),
            ("Attendance Records", total_attendance),
            ("Allocation Records", total_allocations)
        ]

        for row_start in range(0, len(workforce_metrics), 3):

            cols = st.columns(3, gap="medium")

            for col_index, col in enumerate(cols):

                item_index = row_start + col_index

                if item_index >= len(workforce_metrics):
                    continue

                label, value = workforce_metrics[item_index]

                with col:

                    show_metric_card(
                        label,
                        value,
                        "Workforce overview"
                    )

        # =================================================
        # QUALITY AND OPERATIONS
        # =================================================

        st.divider()

        st.subheader("Quality and Operations")

        quality_metrics = [
            ("Defect Records", total_defects),
            ("Station Requirements", total_requirements),
            ("Allocation Audit Records", total_audit)
        ]

        quality_cols = st.columns(3, gap="medium")

        for index, col in enumerate(quality_cols):

            label, value = quality_metrics[index]

            with col:

                show_metric_card(
                    label,
                    value,
                    "Quality and operations overview"
                )

    except Exception as error:

        st.error(
            "Unable to load dashboard data from PostgreSQL."
        )

        st.warning(
            "Check PostgreSQL status and the DB_PASSWORD environment variable."
        )

        with st.expander("Technical error details"):

            st.code(
                f"{type(error).__name__}: {error}"
            )

    # =====================================================
    # PLATFORM CAPABILITIES
    # =====================================================

    st.divider()

    show_platform_capabilities()

    # =====================================================
    # TECHNOLOGY INFORMATION
    # =====================================================

    st.divider()

    with st.container(border=True):

        st.subheader(
            "Powered by Data and Intelligent Automation"
        )

        st.write(
            "Python | Pandas | PostgreSQL | SQLAlchemy | "
            "Streamlit | Plotly | Machine Learning"
        )


# =========================================================
# 9. FEATURE PAGE ROUTING
# =========================================================

PAGE_ROUTES = {

    "Employee Management": (
        "pages.employee_management",
        "show_employee_management"
    ),

    "Attendance Management": (
        "pages.attendance_management",
        "show_attendance_management"
    ),

    "Smart Allocation": (
        "pages.smart_allocation",
        "show_smart_allocation"
    ),

    "Manager Dashboard": (
        "pages.manager_dashboard",
        "show_manager_dashboard"
    ),

    "Workforce Analytics": (
        "pages.workforce_analytics",
        "show_workforce_analytics_page"
    ),

    "Skill Gap Analysis": (
        "pages.skill_gap_analysis",
        "show_skill_gap_analysis_page"
    ),

    "Quality Intelligence": (
        "pages.quality_intelligence",
        "show_quality_intelligence"
    ),

    "Allocation History": (
        "pages.allocation_history",
        "show_allocation_history"
    ),

    "Workforce Data Upload": (
        "pages.workforce_upload",
        "show_workforce_upload"
    )
}


# =========================================================
# 10. DISPLAY SELECTED PAGE
# =========================================================

if selected_page == "Home":

    show_home_dashboard()

else:

    module_name, function_name = PAGE_ROUTES[selected_page]

    try:

        page_module = importlib.import_module(module_name)

        page_module = importlib.reload(page_module)

        page_function = getattr(
            page_module,
            function_name
        )

        page_function()

    except ModuleNotFoundError as error:

        st.error(
            f"Could not load the module for {selected_page}."
        )

        st.code(str(error))

        st.info(
            "Check that the page file exists inside the pages folder "
            "and that its imports are available."
        )

    except AttributeError as error:

        st.error(
            f"The expected page function was not found for {selected_page}."
        )

        st.code(str(error))

    except Exception:

        st.error(
            f"An error occurred while loading {selected_page}."
        )

        with st.expander("Technical error details"):

            st.code(traceback.format_exc())
