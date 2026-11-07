
import pandas as pd


# =====================================================
# EMPLOYEE WORKFORCE VALIDATION
# =====================================================

EMPLOYEE_REQUIRED_COLUMNS = [
    "employee_id",
    "employee_name",
    "experience_years",
    "shift",
    "status"
]


def load_workforce_file(uploaded_file):
    """
    Load and validate employee workforce data.
    Supports CSV and Excel files.
    Does not modify existing project data.
    """

    filename = uploaded_file.name.lower()

    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(uploaded_file)

        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(uploaded_file)

        else:
            return None, ["Unsupported file format. Upload CSV or Excel."]

    except Exception as error:
        return None, [f"Unable to read file: {error}"]

    df.columns = df.columns.str.strip().str.lower()

    errors = []

    # Check required columns
    missing_columns = [
        column for column in EMPLOYEE_REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        errors.append(
            f"Missing required columns: {missing_columns}"
        )
        return df, errors

    # Check missing values
    for column in EMPLOYEE_REQUIRED_COLUMNS:
        if df[column].isnull().any():
            errors.append(
                f"Missing values found in column: {column}"
            )

    # Check duplicate employee IDs
    if df["employee_id"].astype(str).str.strip().duplicated().any():
        errors.append("Duplicate employee IDs found.")

    # Check experience values
    experience = pd.to_numeric(
        df["experience_years"], errors="coerce"
    )

    if experience.isnull().any() or (experience < 0).any():
        errors.append(
            "Experience must contain valid non-negative numbers."
        )

    # Check shift values
    valid_shifts = ["morning", "evening", "night"]

    invalid_shifts = (
        ~df["shift"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(valid_shifts)
    )

    if invalid_shifts.any():
        errors.append("Invalid shift values found.")

    # Check employee status
    valid_statuses = ["active", "inactive"]

    invalid_status = (
        ~df["status"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(valid_statuses)
    )

    if invalid_status.any():
        errors.append("Invalid employee status values found.")

    return df, errors


# =====================================================
# EMPLOYEE SKILLS VALIDATION
# =====================================================

SKILL_REQUIRED_COLUMNS = [
    "employee_id",
    "skill_name",
    "proficiency_level",
    "verification_status"
]


def validate_employee_skills(uploaded_file, employee_df=None):
    """
    Load and validate employee skill records.
    Supports CSV and Excel files.

    Optionally checks whether skill records belong
    to employees in the uploaded employee dataset.
    """

    filename = uploaded_file.name.lower()

    try:
        if filename.endswith(".csv"):
            skills_df = pd.read_csv(uploaded_file)

        elif filename.endswith((".xlsx", ".xls")):
            skills_df = pd.read_excel(uploaded_file)

        else:
            return None, ["Unsupported file format."]

    except Exception as error:
        return None, [f"Unable to read skills file: {error}"]

    skills_df.columns = (
        skills_df.columns.str.strip().str.lower()
    )

    errors = []

    # Check required columns
    missing_columns = [
        column for column in SKILL_REQUIRED_COLUMNS
        if column not in skills_df.columns
    ]

    if missing_columns:
        errors.append(
            f"Missing required columns: {missing_columns}"
        )
        return skills_df, errors

    # Check missing values
    if skills_df[SKILL_REQUIRED_COLUMNS].isnull().any().any():
        errors.append("Missing values found in skill records.")

    # Check duplicate employee-skill combinations
    duplicate_skills = skills_df.duplicated(
        subset=["employee_id", "skill_name"],
        keep=False
    )

    if duplicate_skills.any():
        errors.append("Duplicate employee-skill records found.")

    # Check proficiency levels
    proficiency = pd.to_numeric(
        skills_df["proficiency_level"],
        errors="coerce"
    )

    if proficiency.isnull().any() or (
        ~proficiency.between(1, 5)
    ).any():
        errors.append(
            "Proficiency must be a number between 1 and 5."
        )

    # Check verification status
    valid_statuses = ["verified", "pending"]

    invalid_statuses = (
        ~skills_df["verification_status"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(valid_statuses)
    )

    if invalid_statuses.any():
        errors.append(
            "Invalid skill verification status. "
            "Use Verified or Pending."
        )

    # Check employee IDs against uploaded workforce data
    if employee_df is not None:

        if "employee_id" not in employee_df.columns:
            errors.append(
                "Employee dataset does not contain employee_id."
            )

        else:
            known_ids = set(
                employee_df["employee_id"]
                .astype(str)
                .str.strip()
            )

            uploaded_ids = set(
                skills_df["employee_id"]
                .astype(str)
                .str.strip()
            )

            unknown_ids = uploaded_ids - known_ids

            if unknown_ids:
                errors.append(
                    "Skills reference unknown employee IDs: "
                    f"{sorted(unknown_ids)}"
                )

    return skills_df, errors

def validate_attendance_file(uploaded_file, employee_df=None):
    """
    Load and validate daily employee attendance.
    Supports CSV and Excel files.
    Does not modify existing project data.
    """

    filename = uploaded_file.name.lower()

    try:
        if filename.endswith(".csv"):
            attendance_df = pd.read_csv(uploaded_file)

        elif filename.endswith((".xlsx", ".xls")):
            attendance_df = pd.read_excel(uploaded_file)

        else:
            return None, ["Unsupported attendance file format."]

    except Exception as error:
        return None, [f"Unable to read attendance file: {error}"]

    attendance_df.columns = (
        attendance_df.columns.str.strip().str.lower()
    )

    required_columns = [
        "employee_id",
        "attendance_date",
        "shift",
        "attendance_status"
    ]

    errors = []

    missing_columns = [
        col for col in required_columns
        if col not in attendance_df.columns
    ]

    if missing_columns:
        return attendance_df, [
            f"Missing required columns: {missing_columns}"
        ]

    # Check missing required values
    if attendance_df[required_columns].isnull().any().any():
        errors.append("Missing required attendance values.")

    # Validate attendance dates
    parsed_dates = pd.to_datetime(
        attendance_df["attendance_date"],
        errors="coerce"
    )

    if parsed_dates.isnull().any():
        errors.append("Invalid attendance dates found.")

    # Validate shifts
    valid_shifts = ["morning", "evening", "night"]

    invalid_shifts = (
        ~attendance_df["shift"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(valid_shifts)
    )

    if invalid_shifts.any():
        errors.append("Invalid attendance shifts found.")

    # Validate attendance status
    valid_statuses = ["present", "absent", "leave"]

    invalid_statuses = (
        ~attendance_df["attendance_status"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(valid_statuses)
    )

    if invalid_statuses.any():
        errors.append(
            "Invalid attendance status. "
            "Use Present, Absent or Leave."
        )

    # Check duplicate attendance records
    if attendance_df.duplicated(
        subset=["employee_id", "attendance_date"],
        keep=False
    ).any():
        errors.append(
            "Duplicate attendance records found for an employee and date."
        )

    # Check employee IDs against uploaded workforce
    if employee_df is not None:

        known_ids = set(
            employee_df["employee_id"]
            .astype(str)
            .str.strip()
        )

        uploaded_ids = set(
            attendance_df["employee_id"]
            .astype(str)
            .str.strip()
        )

        unknown_ids = uploaded_ids - known_ids

        if unknown_ids:
            errors.append(
                f"Attendance references unknown employee IDs: "
                f"{sorted(unknown_ids)}"
            )

    return attendance_df, errors
