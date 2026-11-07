
from add_employee import add_employee
from add_employee_skills import add_employee_skill


def register_employee_with_skills(
    name,
    experience,
    shift,
    skill_list=None
):

    # 1. Validate employee details
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Employee name cannot be empty.")

    if not isinstance(experience, (int, float)) or experience < 0:
        raise ValueError("Experience cannot be negative.")

    if shift not in ["Morning", "Evening", "Night"]:
        raise ValueError("Invalid employee shift.")

    # 2. Allow registration without skills
    if skill_list is None:
        skill_list = []

    if not isinstance(skill_list, list):
        raise ValueError("Skills must be provided as a list.")

    # 3. Validate all skills BEFORE employee creation
    validated_skills = []
    seen_skills = set()

    for item in skill_list:

        if not isinstance(item, (tuple, list)) or len(item) != 2:
            raise ValueError("Each skill must contain a name and proficiency.")

        skill_name, proficiency = item

        if not isinstance(skill_name, str) or not skill_name.strip():
            raise ValueError("Skill name cannot be empty.")

        skill_name = skill_name.strip()

        if (
            not isinstance(proficiency, int)
            or isinstance(proficiency, bool)
            or not 1 <= proficiency <= 5
        ):
            raise ValueError(
                f"Invalid proficiency for {skill_name}. Use 1 to 5."
            )

        if skill_name.lower() in seen_skills:
            raise ValueError(f"Duplicate skill: {skill_name}")

        seen_skills.add(skill_name.lower())
        validated_skills.append((skill_name, proficiency))

    # 4. Create employee only after all validation passes
    employee_id = add_employee(
        name,
        experience,
        shift
    )

    # 5. Add skills
    for skill_name, proficiency in validated_skills:
        add_employee_skill(
            employee_id,
            skill_name,
            proficiency
        )

    print("\nEmployee registration completed successfully.")
    print("Employee ID:", employee_id)

    return employee_id


if __name__ == "__main__":
    print("Employee management module is ready.")

