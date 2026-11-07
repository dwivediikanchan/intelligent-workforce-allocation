
import streamlit as st
import pandas as pd

from employee_management import register_employee_with_skills
from add_employee_skills import add_employee_skill
from manage_employee_skills import update_employee_skill
from verify_employee_skills import verify_employee_skill

from database_repository import (
    get_employees,
    get_employee_skills
)


def show_employee_management():

    st.title("👥 Employee Management")
    st.caption("Register employees and manage their skills and verification.")

    employees = get_employees()
    skills = get_employee_skills()

    tab1, tab2, tab3, tab4 = st.tabs([
        "Register Employee",
        "Add Skill",
        "Update Skill",
        "Verify Skill"
    ])

    # ------------------------------------------
    # TAB 1: REGISTER EMPLOYEE
    # ------------------------------------------

    with tab1:

        st.subheader("Register New Employee")

        with st.form("register_employee_form"):

            name = st.text_input("Employee Name")
            experience = st.number_input(
                "Experience (Years)",
                min_value=0,
                step=1
            )

            shift = st.selectbox(
                "Shift",
                ["Morning", "Evening", "Night"]
            )

            skill_count = st.number_input(
                "Number of Initial Skills",
                min_value=0,
                max_value=10,
                value=0,
                step=1
            )

            initial_skills = []

            for i in range(int(skill_count)):

                st.markdown(f"**Skill {i + 1}**")

                col1, col2 = st.columns(2)

                with col1:
                    skill_name = st.text_input(
                        "Skill Name",
                        key=f"register_skill_name_{i}"
                    )

                with col2:
                    proficiency = st.selectbox(
                        "Proficiency",
                        [1, 2, 3, 4, 5],
                        key=f"register_skill_level_{i}"
                    )

                initial_skills.append((skill_name, proficiency))

            submitted = st.form_submit_button(
                "Register Employee",
                use_container_width=True
            )

            if submitted:

                try:
                    if any(not skill.strip() for skill, _ in initial_skills):
                        raise ValueError("Enter a name for every initial skill.")

                    employee_id = register_employee_with_skills(
                        name=name,
                        experience=experience,
                        shift=shift,
                        skill_list=initial_skills
                    )

                    st.success(
                        f"Employee registered successfully. Employee ID: {employee_id}"
                    )

                    st.rerun()

                except Exception as error:
                    st.error(str(error))

    # ------------------------------------------
    # TAB 2: ADD SKILL
    # ------------------------------------------

    with tab2:

        st.subheader("Add Skill to Existing Employee")

        if employees.empty:

            st.warning("No employees found.")

        else:

            employee_options = {
                f"{row.employee_id} - {row.employee_name}": row.employee_id
                for row in employees.itertuples()
            }

            with st.form("add_skill_form"):

                selected_employee = st.selectbox(
                    "Select Employee",
                    list(employee_options.keys())
                )

                skill_name = st.text_input("Skill Name")

                proficiency = st.selectbox(
                    "Proficiency Level",
                    [1, 2, 3, 4, 5]
                )

                submitted = st.form_submit_button(
                    "Add Skill",
                    use_container_width=True
                )

                if submitted:

                    try:
                        add_employee_skill(
                            employee_options[selected_employee],
                            skill_name,
                            proficiency
                        )

                        st.success("Skill added successfully. Verification is Pending.")
                        st.rerun()

                    except Exception as error:
                        st.error(str(error))

    # ------------------------------------------
    # TAB 3: UPDATE SKILL
    # ------------------------------------------

    with tab3:

        st.subheader("Update Employee Skill")

        if skills.empty:

            st.warning("No employee skills found.")

        else:

            employee_ids = sorted(skills["employee_id"].unique())

            selected_id = st.selectbox(
                "Select Employee ID",
                employee_ids,
                key="update_employee_id"
            )

            employee_skill_rows = skills[
                skills["employee_id"] == selected_id
            ]

            skill_options = employee_skill_rows["skill_name"].tolist()

            selected_skill = st.selectbox(
                "Select Skill",
                skill_options,
                key="update_skill_name"
            )

            current_level = int(
                employee_skill_rows.loc[
                    employee_skill_rows["skill_name"] == selected_skill,
                    "proficiency_level"
                ].iloc[0]
            )

            new_level = st.selectbox(
                "New Proficiency Level",
                [1, 2, 3, 4, 5],
                index=current_level - 1
            )

            if st.button("Update Skill", use_container_width=True):

                try:
                    update_employee_skill(
                        selected_id,
                        selected_skill,
                        new_level
                    )

                    st.success(
                        "Skill updated. If proficiency changed, verification is now Pending."
                    )

                    st.rerun()

                except Exception as error:
                    st.error(str(error))

    # ------------------------------------------
    # TAB 4: VERIFY SKILL
    # ------------------------------------------

    with tab4:

        st.subheader("Verify Employee Skill")

        if skills.empty:

            st.warning("No employee skills found.")

        else:

            pending_skills = skills[
                skills["verification_status"] != "Verified"
            ]

            if pending_skills.empty:

                st.success("All employee skills are verified.")

            else:

                pending_options = {
                    (
                        f"{row.employee_id} - {row.skill_name} "
                        f"(Level {row.proficiency_level})"
                    ): (row.employee_id, row.skill_name)
                    for row in pending_skills.itertuples()
                }

                selected_pending = st.selectbox(
                    "Select Skill to Verify",
                    list(pending_options.keys())
                )

                if st.button("Verify Skill", use_container_width=True):

                    try:
                        employee_id, skill_name = pending_options[selected_pending]

                        verify_employee_skill(
                            employee_id,
                            skill_name
                        )

                        st.success("Skill verified successfully.")
                        st.rerun()

                    except Exception as error:
                        st.error(str(error))

    # ------------------------------------------
    # EMPLOYEE AND SKILL REGISTRY
    # ------------------------------------------

    st.divider()
    st.subheader("Employee Registry")

    employees = get_employees()
    skills = get_employee_skills()

    if not employees.empty:

        st.dataframe(
            employees,
            use_container_width=True,
            hide_index=True
        )

    st.subheader("Employee Skill Registry")

    if not skills.empty:

        st.dataframe(
            skills,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No employee skills available.")
