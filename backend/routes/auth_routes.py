from flask import Blueprint, request, jsonify, g
from backend.extensions import db, bcrypt
from backend.models import User, Student, Company
from backend.auth import create_token, login_required
from backend.validators import valid_email, valid_float, valid_int, require_fields

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    role = (data.get("role") or "").strip().lower()
    if role not in ("student", "company"):
        return jsonify({"error": "Role must be student or company."}), 400

    email, err = valid_email(data.get("email"))
    if err:
        return jsonify({"error": err}), 400

    password = data.get("password") or ""
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists."}), 409

    user = User(email=email,
                password=bcrypt.generate_password_hash(password).decode("utf-8"),
                role=role)
    db.session.add(user)
    db.session.flush()

    if role == "student":
        missing = require_fields(data, ["name", "roll_number"])
        if missing:
            db.session.rollback()
            return jsonify({"error": missing}), 400
        if Student.query.filter_by(roll_number=data["roll_number"].strip()).first():
            db.session.rollback()
            return jsonify({"error": "Roll number already registered."}), 409
        cgpa, err = valid_float(data.get("cgpa"), "CGPA", lo=0, hi=10)
        if err:
            db.session.rollback()
            return jsonify({"error": err}), 400
        year, err = valid_int(data.get("year"), "Year", lo=1, hi=6)
        if err:
            db.session.rollback()
            return jsonify({"error": err}), 400
        db.session.add(Student(
            user_id=user.id,
            name=data["name"].strip(),
            roll_number=data["roll_number"].strip(),
            department=(data.get("department") or "").strip(),
            year=year,
            cgpa=cgpa,
            skills=(data.get("skills") or "").strip(),
            experience=(data.get("experience") or "").strip(),
        ))
        msg = "Registration successful! You can now log in."
    else:  # company
        missing = require_fields(data, ["company_name"])
        if missing:
            db.session.rollback()
            return jsonify({"error": missing}), 400
        db.session.add(Company(
            user_id=user.id,
            company_name=data["company_name"].strip(),
            industry=(data.get("industry") or "").strip(),
            location=(data.get("location") or "").strip(),
            hr_contact=(data.get("hr_contact") or "").strip(),
            website=(data.get("website") or "").strip(),
            description=(data.get("description") or "").strip(),
        ))
        msg = "Registration submitted. Await admin approval before logging in."

    db.session.commit()
    return jsonify({"message": msg}), 201


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Invalid email or password."}), 401
    if not user.is_active:
        return jsonify({"error": "Your account is deactivated."}), 403
    # Milestone 6: "only approved companies can create placement drives" is enforced.
    if user.role == "company":
        if user.company.is_blacklisted:
            return jsonify({"error": "Your company account has been blacklisted."}), 403
        if not user.company.is_approved:
            return jsonify({"error": "Admin approval pending for your account."}), 403
    if user.role == "student" and user.student.is_blacklisted:
        return jsonify({"error": "Your account has been blacklisted."}), 403

    token = create_token(user)
    profile = None
    if user.role == "student":
        profile = user.student.to_dict()
    elif user.role == "company":
        profile = user.company.to_dict()
    return jsonify({"token": token, "user": user.to_dict(), "profile": profile})


@bp.get("/me")
@login_required
def me():
    user = g.current_user
    profile = None
    if user.role == "student":
        profile = user.student.to_dict()
    elif user.role == "company":
        profile = user.company.to_dict()
    return jsonify({"user": user.to_dict(), "profile": profile})
