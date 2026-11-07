from sqlalchemy import CheckConstraint
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Date,
    Time,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
    JSON
)

from database_connection import Base


class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(String(20), primary_key=True)
    employee_name = Column(String(100), nullable=False)
    experience_years = Column(Float, nullable=False)
    shift = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)


class EmployeeSkill(Base):
    __tablename__ = "employee_skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(
        String(20),
        ForeignKey("employees.employee_id"),
        nullable=False
    )
    skill_name = Column(String(100), nullable=False)
    proficiency_level = Column(Integer, nullable=False)
    verification_status = Column(String(20), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "skill_name",
            name="uq_employee_skill"
        ),
    )


class Station(Base):
    __tablename__ = "stations"

    station_id = Column(String(20), primary_key=True)
    station_name = Column(String(100), nullable=False)
    subassembly = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=False)


class StationRequirement(Base):
    __tablename__ = "station_requirements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(
        String(20),
        ForeignKey("stations.station_id"),
        nullable=False
    )
    skill_name = Column(String(100), nullable=False)
    min_proficiency = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)
    mandatory = Column(Boolean, nullable=False)


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(
        String(20),
        ForeignKey("employees.employee_id"),
        nullable=False
    )
    attendance_date = Column(Date, nullable=False)
    shift = Column(String(20), nullable=False)
    attendance_status = Column(String(20), nullable=False)
    check_in = Column(Time, nullable=True)
    check_out = Column(Time, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "attendance_date",
            name="uq_employee_attendance_date"
        ),
    )


class Allocation(Base):
    __tablename__ = "allocations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(
        String(20),
        ForeignKey("employees.employee_id"),
        nullable=False
    )
    station_id = Column(
        String(20),
        ForeignKey("stations.station_id"),
        nullable=False
    )
    allocation_date = Column(Date, nullable=True)
    shift = Column(String(20), nullable=False)
    skill_score = Column(Float, nullable=False)
    status = Column(String(20), nullable=False)


class AllocationAudit(Base):
    __tablename__ = "allocation_audit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
    manager_id = Column(String(50), nullable=False)
    employee_id = Column(
        String(20),
        ForeignKey("employees.employee_id"),
        nullable=False
    )
    shift = Column(String(20), nullable=False)
    old_station_id = Column(String(20), nullable=True)
    new_station_id = Column(String(20), nullable=True)
    skill_score = Column(Float, nullable=True)
    action = Column(String(50), nullable=False)
    allocation_date = Column(Date, nullable=True)


class SkillVerificationRecommendation(Base):
    __tablename__ = "skill_verification_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)

    employee_id = Column(
        String(20),
        ForeignKey("employees.employee_id"),
        nullable=False
    )

    recommended_station = Column(
        String(20),
        ForeignKey("stations.station_id"),
        nullable=False
    )

    skills_to_verify = Column(JSON, nullable=False)

    recommendation_status = Column(
        String(50),
        nullable=False,
        default="Pending Manager Approval"
    )

    manager_id = Column(String(50), nullable=True)

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    approved_at = Column(DateTime, nullable=True)

    completed_at = Column(DateTime, nullable=True)

class DefectRecord(Base):
    __tablename__ = "defect_records"

    defect_id = Column(String(20), primary_key=True)

    production_date = Column(Date, nullable=False)

    station_id = Column(
        String(20),
        ForeignKey("stations.station_id"),
        nullable=False
    )

    defect_type = Column(String(150), nullable=False)

    defect_count = Column(Integer, nullable=False)

    units_inspected = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "defect_count >= 0",
            name="ck_defect_count_nonnegative"
        ),
        CheckConstraint(
            "units_inspected > 0",
            name="ck_units_inspected_positive"
        ),
    )
