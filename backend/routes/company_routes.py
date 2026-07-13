import os
from flask import Blueprint, request, jsonify, g, send_from_directory
from sqlalchemy import func
from backend.extensions import db
from backend.config import Config
from backend.models import PlacementDrive, Application, Interview, Placement
from backend.auth import role_required
from backend.cache import cache_clear_prefix
from backend.validators import (require_fields, valid_float, valid_int,
                                valid_date_eod, valid_datetime)

bp = Blueprint("company", __name__, url_prefix="/api/company")
# Milestone 6: whitelist of allowed application statuses.
VALID_STATUSES = ("Applied", "Shortlisted", "Interview", "Selected", "Rejected", "Placed")

"""
    Milestone 6: scoping for 'Company can view applications' — ensures a
    company can only access drives (and therefore applicants) that belong
    to them. Prevents one company from reading another company's
    applicant data via the API.
"""
def _own_drive_or_404(did):
    d = PlacementDrive.query.get_or_404(did)
    if d.company_id != g.current_user.company.id:
        return None, (jsonify({"error": "Forbidden"}), 403)
    return d, None


@bp.get("/dashboard")
@role_required("company")
def dashboard():
    c = g.current_user.company
    drives = PlacementDrive.query.filter_by(company_id=c.id).all()
    total_apps = Application.query.join(PlacementDrive)\
        .filter(PlacementDrive.company_id == c.id).count()
    shortlisted = Application.query.join(PlacementDrive)\
        .filter(PlacementDrive.company_id == c.id,
                Application.application_status == "Shortlisted").count()
    status_rows = db.session.query(
        Application.application_status, func.count(Application.id)
    ).join(PlacementDrive).filter(PlacementDrive.company_id == c.id)\
     .group_by(Application.application_status).all()
    status_distribution = {status: count for status, count in status_rows}
    return jsonify({
        "company": c.to_dict(),
        "drives": [d.to_dict() for d in drives],
        "total_drives": len(drives),
        "total_applications": total_apps,
        "shortlisted": shortlisted,
        "status_distribution": status_distribution,
    })


@bp.get("/drives")
@role_required("company")
def list_drives():
    c = g.current_user.company
    drives = PlacementDrive.query.filter_by(company_id=c.id)\
        .order_by(PlacementDrive.created_at.desc()).all()
    return jsonify([d.to_dict() for d in drives])

# Milestone 6: no explicit "is_approved" check needed here.
@bp.post("/drives")
@role_required("company")
def create_drive():
    data = request.get_json(silent=True) or {}
    missing = require_fields(data, ["title", "job_role"])
    if missing:
        return jsonify({"error": missing}), 400

    package, err = valid_float(data.get("package"), "Package", lo=0)
    if err:
        return jsonify({"error": err}), 400
    elig_cgpa, err = valid_float(data.get("eligibility_cgpa"), "Eligibility CGPA", lo=0, hi=10)
    if err:
        return jsonify({"error": err}), 400
    elig_year, err = valid_int(data.get("eligibility_year"), "Eligibility year", lo=1, hi=6)
    if err:
        return jsonify({"error": err}), 400
    deadline, err = valid_date_eod(data.get("application_deadline"), "Application deadline")
    if err:
        return jsonify({"error": err}), 400
    drive_date, err = valid_date_eod(data.get("drive_date"), "Drive date")
    if err:
        return jsonify({"error": err}), 400

    d = PlacementDrive(
        company_id=g.current_user.company.id,
        title=data["title"].strip(),
        job_role=data["job_role"].strip(),
        description=(data.get("description") or "").strip(),
        skills_required=(data.get("skills_required") or "").strip(),
        package=package,
        eligibility_cgpa=elig_cgpa,
        eligibility_branch=(data.get("eligibility_branch") or "").strip(),
        eligibility_year=elig_year,
        eligibility_criteria=(data.get("eligibility_criteria") or "").strip(),
        application_deadline=deadline,
        drive_date=drive_date,
    )
    db.session.add(d)
    db.session.commit()
    cache_clear_prefix("drives:")
    return jsonify({"message": "Drive submitted for admin approval.", "drive": d.to_dict()}), 201


@bp.get("/drives/<int:did>")
@role_required("company")
def view_drive(did):
    d, err = _own_drive_or_404(did)
    if err:
        return err
    return jsonify({
        "drive": d.to_dict(),
        "applications": [a.to_dict() for a in d.applications],
        "interviews": [iv.to_dict() for iv in d.interviews],
    })


@bp.post("/drives/<int:did>/close")
@role_required("company")
def close_drive(did):
    d, err = _own_drive_or_404(did)
    if err:
        return err
    d.drive_status = "Closed"
    db.session.commit()
    cache_clear_prefix("drives:")
    return jsonify({"message": "Drive closed."})

# Milestone 6: status update
@bp.post("/applications/<int:aid>/status")
@role_required("company")
def update_application(aid):
    a = Application.query.get_or_404(aid)
    if a.drive.company_id != g.current_user.company.id:
        return jsonify({"error": "Forbidden"}), 403
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    if new_status not in VALID_STATUSES:
        return jsonify({"error": "Invalid status."}), 400
    a.application_status = new_status
    a.remark = (data.get("remark") or "").strip()

    new_placement_id = None
    if new_status in ("Selected", "Placed") and not a.placement:
        placement = Placement(
            application_id=a.id,
            student_id=a.student_id,
            company_id=a.drive.company_id,
            position=a.drive.job_role,
            salary=a.drive.package,
        )
        db.session.add(placement)
        db.session.flush()
        new_placement_id=placement.id
    db.session.commit()
    if new_placement_id:
        try:
            from backend.jobs.tasks import generate_offer_letter
            generate_offer_letter.delay(new_placement_id)
        except Exception as e:
            print(f"[offer-letter] could not queue generation: {e}")

    return jsonify({"message": "Application updated.", "application": a.to_dict()})

# Milestone 6: scheduling an interview auto-advances a fresh application
@bp.post("/drives/<int:did>/interviews")
@role_required("company")
def schedule_interview(did):
    d, err = _own_drive_or_404(did)
    if err:
        return err
    data = request.get_json(silent=True) or {}
    student_id, verr = valid_int(data.get("student_id"), "Student", required=True)
    if verr:
        return jsonify({"error": verr}), 400
    when, err = valid_datetime(data.get("scheduled_at"), "Interview time", required=True)
    if err:
        return jsonify({"error": err}), 400
    # student must have applied to this drive
    app = Application.query.filter_by(drive_id=did, student_id=student_id).first()
    if not app:
        return jsonify({"error": "That student has not applied to this drive."}), 400

    iv = Interview(
        drive_id=did, student_id=student_id, scheduled_at=when,
        mode=(data.get("mode") or "In-person").strip(),
        location=(data.get("location") or "").strip(),
    )
    if app.application_status in ("Applied","Shortlisted"):
        app.application_status = "Interview"
    db.session.add(iv)
    db.session.commit()
    return jsonify({"message": "Interview scheduled.", "interview": iv.to_dict()}), 201


@bp.post("/interviews/<int:iid>/feedback")
@role_required("company")
def interview_feedback(iid):
    iv = Interview.query.get_or_404(iid)
    if iv.drive.company_id != g.current_user.company.id:
        return jsonify({"error": "Forbidden"}), 403
    data = request.get_json(silent=True) or {}
    iv.feedback = (data.get("feedback") or "").strip()
    db.session.commit()
    return jsonify({"message": "Feedback saved."})
