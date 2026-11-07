
from database_repository import get_employee_skills

skills = get_employee_skills()

if skills.empty:
    print("No employee skill records found in PostgreSQL.")
    raise SystemExit

print("\n========== EMPLOYEE SKILL DATA ==========")
print(skills.to_string(index=False))

print("\n========== VERIFICATION SUMMARY ==========")
print(skills["verification_status"].value_counts())

print("\n========== EMPLOYEE SKILL COUNTS ==========")
print(
    skills.groupby("employee_id")["skill_name"]
    .count()
)
