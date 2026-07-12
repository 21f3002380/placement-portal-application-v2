from datetime import datetime, date
from backend.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin / company / student
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student", backref="user", uselist=False,
                              cascade="all, delete-orphan")
    company = db.relationship("Company", backref="user", uselist=False,
                              cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
        }


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)

    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(50), unique=True, nullable=False)
    department = db.Column(db.String(100))
    year = db.Column(db.Integer)
    cgpa = db.Column(db.Float)
    skills = db.Column(db.Text)
    experience = db.Column(db.Text)
    resume_filename = db.Column(db.String(300))
    is_blacklisted = db.Column(db.Boolean, default=False)

    applications = db.relationship("Application", backref="student", lazy=True,
                                   cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "email": self.user.email if self.user else None,
            "name": self.name,
            "roll_number": self.roll_number,
            "department": self.department,
            "year": self.year,
            "cgpa": self.cgpa,
            "skills": self.skills,
            "experience": self.experience,
            "resume_filename": self.resume_filename,
            "is_blacklisted": self.is_blacklisted,
        }


class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)

    company_name = db.Column(db.String(120), nullable=False)
    industry = db.Column(db.String(120))
    location = db.Column(db.String(120))
    description = db.Column(db.Text)
    website = db.Column(db.String(200))
    hr_contact = db.Column(db.String(120))
    is_approved = db.Column(db.Boolean, default=False)
    is_blacklisted = db.Column(db.Boolean, default=False)

    drives = db.relationship("PlacementDrive", backref="company", lazy=True,
                             cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "email": self.user.email if self.user else None,
            "company_name": self.company_name,
            "industry": self.industry,
            "location": self.location,
            "description": self.description,
            "website": self.website,
            "hr_contact": self.hr_contact,
            "is_approved": self.is_approved,
            "is_blacklisted": self.is_blacklisted,
        }


class PlacementDrive(db.Model):
    __tablename__ = "placement_drives"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)

    title = db.Column(db.String(150), nullable=False)
    job_role = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    skills_required = db.Column(db.Text)
    package = db.Column(db.Float)
    eligibility_cgpa = db.Column(db.Float)
    eligibility_branch = db.Column(db.String(200))   # comma-separated, blank = all
    eligibility_year = db.Column(db.Integer)         # min year, null = any
    eligibility_criteria = db.Column(db.Text)
    application_deadline = db.Column(db.DateTime)
    drive_date = db.Column(db.DateTime)
    drive_status = db.Column(db.String(20), default="Open")       # Open / Closed
    approval_status = db.Column(db.String(20), default="Pending")  # Pending/Approved/Rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship("Application", backref="drive", lazy=True,
                                   cascade="all, delete-orphan")
    interviews = db.relationship("Interview", backref="drive", lazy=True,
                                 cascade="all, delete-orphan")

    def to_dict(self, include_company=True):
        d = {
            "id": self.id,
            "company_id": self.company_id,
            "title": self.title,
            "job_role": self.job_role,
            "description": self.description,
            "skills_required": self.skills_required,
            "package": self.package,
            "eligibility_cgpa": self.eligibility_cgpa,
            "eligibility_branch": self.eligibility_branch,
            "eligibility_year": self.eligibility_year,
            "eligibility_criteria": self.eligibility_criteria,
            "application_deadline": self.application_deadline.isoformat() if self.application_deadline else None,
            "drive_date": self.drive_date.isoformat() if self.drive_date else None,
            "drive_status": self.drive_status,
            "approval_status": self.approval_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "applicant_count": len(self.applications),
        }
        if include_company and self.company:
            d["company_name"] = self.company.company_name
            d["company_location"] = self.company.location
        return d


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey("placement_drives.id"), nullable=False)

    # Applied / Shortlisted / Interview / Selected / Rejected / Placed
    # Milestone 6: status lifecycle — Applied / Shortlisted / Interview / Selected / Rejected / Placed.
    # This project uses "Selected" instead of "Offer"
    application_status = db.Column(db.String(20), default="Applied")
    remark = db.Column(db.Text)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

    placement = db.relationship("Placement", backref="application", uselist=False,
                                cascade="all, delete-orphan")
    
    # Milestone 6: DB-level guarantee against duplicate applications
    __table_args__ = (
        db.UniqueConstraint("student_id", "drive_id", name="unique_student_drive"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student.name if self.student else None,
            "student_department": self.student.department if self.student else None,
            "student_cgpa": self.student.cgpa if self.student else None,
            "drive_id": self.drive_id,
            "drive_title": self.drive.title if self.drive else None,
            "job_role": self.drive.job_role if self.drive else None,
            "company_name": self.drive.company.company_name if self.drive and self.drive.company else None,
            "application_status": self.application_status,
            "remark": self.remark,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
        }


class Interview(db.Model):
    __tablename__ = "interviews"

    id = db.Column(db.Integer, primary_key=True)
    drive_id = db.Column(db.Integer, db.ForeignKey("placement_drives.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)

    scheduled_at = db.Column(db.DateTime, nullable=False)
    mode = db.Column(db.String(30), default="In-person")  # In-person / Online
    location = db.Column(db.String(200))
    feedback = db.Column(db.Text)
    reminder_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student")

    def to_dict(self):
        return {
            "id": self.id,
            "drive_id": self.drive_id,
            "drive_title": self.drive.title if self.drive else None,
            "student_id": self.student_id,
            "student_name": self.student.name if self.student else None,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "mode": self.mode,
            "location": self.location,
            "feedback": self.feedback,
        }


class Placement(db.Model):
    __tablename__ = "placements"

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"),
                               nullable=False, unique=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)

    position = db.Column(db.String(120))
    salary = db.Column(db.Float)
    joining_date = db.Column(db.Date)
    offer_filename = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student")
    company = db.relationship("Company")

    def to_dict(self):
        return {
            "id": self.id,
            "application_id": self.application_id,
            "student_id": self.student_id,
            "student_name": self.student.name if self.student else None,
            "company_id": self.company_id,
            "company_name": self.company.company_name if self.company else None,
            "position": self.position,
            "salary": self.salary,
            "joining_date": self.joining_date.isoformat() if self.joining_date else None,
            "offer_filename": self.offer_filename,
        }
