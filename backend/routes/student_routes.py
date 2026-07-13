import os
from datetime import datetime
from flask import Blueprint, request, jsonify, g, send_from_directory
from werkzeug.utils import secure_filename
from backend.extensions import db
from backend.config import Config
from backend.models import (PlacementDrive, Application, Interview, Placement,
                            Student, Company)
from backend.auth import role_required, login_required
from backend.cache import cached, cache_clear_prefix
from backend.validators import valid_float, valid_int

bp = Blueprint("student", __name__, url_prefix="/api/student")


def file_allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() == "pdf"


def _eligible(student, drive):
    """Return (ok, reason)."""
    if student.is_blacklisted:
        return False, "Your account has been blacklisted."
    if drive.drive_status != "Open":
        return False, "This drive is no longer accepting applications."
    if drive.application_deadline and datetime.now() > drive.application_deadline:
        return False, "The application deadline has passed."
    if drive.eligibility_cgpa and (student.cgpa or 0) < drive.eligibility_cgpa:
        return False, f"Requires a minimum CGPA of {drive.eligibility_cgpa}."
    if drive.eligibility_year and (student.year or 0) < drive.eligibility_year:
        return False, f"Requires year {drive.eligibility_year} or above."
    if drive.eligibility_branch:
        allowed = [b.strip().lower() for b in drive.eligibility_branch.split(",") if b.strip()]
        if allowed and (student.department or "").lower() not in allowed:
            return False, "Your department is not eligible for this drive."
    return True, ""


@bp.get("/dashboard")
@role_required("student")
def dashboard():
    s = g.current_user.student
    apps = Application.query.filter_by(student_id=s.id).all()
    status_distribution = {}
    for a in apps:
        status_distribution[a.application_status] = status_distribution.get(a.application_status, 0) + 1
    return jsonify({
        "student": s.to_dict(),
        "companies": [c.to_dict() for c in
                      Company.query.filter_by(is_approved=True, is_blacklisted=False).all()],
        "applications": [a.to_dict() for a in
                         sorted(apps, key=lambda a: a.applied_at or 0, reverse=True)],
        "status_distribution": status_distribution,
    })


@bp.get("/drives")
@role_required("student")
@cached(lambda: "drives:student:" + str(g.current_user.student.id) + ":"
               + request.args.get("q", "").strip().lower(), timeout=30)
def drives():
    q = request.args.get("q", "").strip()
    query = PlacementDrive.query.filter_by(approval_status="Approved", drive_status="Open")
    if q:
        query = query.join(Company).filter(db.or_(
            PlacementDrive.title.ilike(f"%{q}%"),
            PlacementDrive.job_role.ilike(f"%{q}%"),
            PlacementDrive.skills_required.ilike(f"%{q}%"),
            Company.company_name.ilike(f"%{q}%"),
        ))
    s = g.current_user.student
    applied_ids = {a.drive_id for a in s.applications}
    result = []
    for d in query.order_by(PlacementDrive.created_at.desc()).all():
        item = d.to_dict()
        item["already_applied"] = d.id in applied_ids
        ok, reason = _eligible(s, d)
        item["eligible"] = ok
        item["ineligible_reason"] = reason
        result.append(item)
    return result


@bp.post("/drives/<int:did>/apply")
@role_required("student")
def apply(did):
    s = g.current_user.student
    d = PlacementDrive.query.get_or_404(did)
    if d.approval_status != "Approved":
        return jsonify({"error": "This drive is not open for applications."}), 400
    ok, reason = _eligible(s, d)
    if not ok:
        return jsonify({"error": reason}), 400
    if Application.query.filter_by(student_id=s.id, drive_id=did).first():
        return jsonify({"error": "You have already applied for this drive."}), 409
    a = Application(student_id=s.id, drive_id=did)
    db.session.add(a)
    db.session.commit()
    cache_clear_prefix(f"drives:student:{s.id}:")
    return jsonify({"message": f"Applied for {d.title}.", "application": a.to_dict()}), 201


@bp.get("/applications")
@role_required("student")
def applications():
    s = g.current_user.student
    apps = Application.query.filter_by(student_id=s.id)\
        .order_by(Application.applied_at.desc()).all()
    return jsonify([a.to_dict() for a in apps])


@bp.get("/interviews")
@role_required("student")
def interviews():
    s = g.current_user.student
    ivs = Interview.query.filter_by(student_id=s.id)\
        .order_by(Interview.scheduled_at.asc()).all()
    return jsonify([iv.to_dict() for iv in ivs])


@bp.get("/placements")
@role_required("student")
def placements():
    s = g.current_user.student
    ps = Placement.query.filter_by(student_id=s.id).all()
    return jsonify([p.to_dict() for p in ps])


@bp.put("/profile")
@role_required("student")
def update_profile():
    s = g.current_user.student
    data = request.get_json(silent=True) or {}
    cgpa, err = valid_float(data.get("cgpa"), "CGPA", lo=0, hi=10)
    if err:
        return jsonify({"error": err}), 400
    year, err = valid_int(data.get("year"), "Year", lo=1, hi=6)
    if err:
        return jsonify({"error": err}), 400
    if "name" in data:
        s.name = (data.get("name") or s.name).strip()
    s.department = (data.get("department") or s.department or "").strip()
    if cgpa is not None:
        s.cgpa = cgpa
    if year is not None:
        s.year = year
    s.skills = (data.get("skills") or s.skills or "").strip()
    s.experience = (data.get("experience") or s.experience or "").strip()
    db.session.commit()
    return jsonify({"message": "Profile updated.", "profile": s.to_dict()})


@bp.post("/resume")
@role_required("student")
def upload_resume():
    s = g.current_user.student
    resume = request.files.get("resume")
    if not resume or not file_allowed(resume.filename):
        return jsonify({"error": "Please upload a PDF file."}), 400
    filename = secure_filename(f"{s.roll_number}.pdf")
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    resume.save(os.path.join(Config.UPLOAD_FOLDER, filename))
    s.resume_filename = filename
    db.session.commit()
    return jsonify({"message": "Resume uploaded.", "resume_filename": filename})


@bp.post("/export")
@role_required("student")
def export_csv():
    """Trigger async CSV export via Celery."""
    s = g.current_user.student
    try:
        from backend.jobs.tasks import export_applications_csv
        task = export_applications_csv.delay(s.id)
        return jsonify({"message": "Export started. You'll be alerted when ready.",
                        "task_id": task.id}), 202
    except Exception as e:
        return jsonify({"error": f"Could not start export (is Celery/Redis running?): {e}"}), 503


@bp.get("/export/<task_id>/status")
@role_required("student")
def export_status(task_id):
    try:
        from run import celery
        res = celery.AsyncResult(task_id)
        return jsonify({"state": res.state,
                        "result": res.result if res.ready() else None})
    except Exception as e:
        return jsonify({"error": str(e)}), 503


@bp.get("/resume/<int:student_id>")
@login_required
def download_resume(student_id):
    student = Student.query.get_or_404(student_id)
    user = g.current_user
    if user.role == "student" and user.student.id != student_id:
        return jsonify({"error": "Forbidden"}), 403
    if user.role == "company":
        applied = Application.query.join(PlacementDrive).filter(
            Application.student_id == student_id,
            PlacementDrive.company_id == user.company.id).first()
        if not applied:
            return jsonify({"error": "Forbidden"}), 403
    if not student.resume_filename:
        return jsonify({"error": "No resume on file."}), 404
    return send_from_directory(Config.UPLOAD_FOLDER, student.resume_filename)


@bp.get("/export/download/<path:filename>")
@role_required("student")
def download_export(filename):
    return send_from_directory(Config.EXPORT_FOLDER, secure_filename(filename),
                               as_attachment=True)


@bp.get("/placements/<int:placement_id>/offer")
@login_required
def download_offer(placement_id):
    """
    Download the offer letter / placement confirmation for a Placement.
    Accessible to: the owning student, admin, or the company that made
    the placement (same ownership pattern as resume download).
    """
    placement = Placement.query.get_or_404(placement_id)
    user = g.current_user
    if user.role == "student" and user.student.id != placement.student_id:
        return jsonify({"error": "Forbidden"}), 403
    if user.role == "company" and user.company.id != placement.company_id:
        return jsonify({"error": "Forbidden"}), 403
    if not placement.offer_filename:
        return jsonify({"error": "Offer letter not yet generated."}), 404
    return send_from_directory(Config.OFFER_FOLDER, placement.offer_filename)


@bp.get("/companies")
@role_required("student")
@cached(lambda: "student:companies:" + request.args.get("q", "").strip().lower(), timeout=60)
def search_companies():
    q = request.args.get("q", "").strip()
    query = Company.query.filter_by(is_approved=True, is_blacklisted=False)
    if q:
        query = query.filter(db.or_(
            Company.company_name.ilike(f"%{q}%"),
            Company.industry.ilike(f"%{q}%"),
            Company.location.ilike(f"%{q}%"),
        ))
    return [c.to_dict() for c in query.order_by(Company.company_name).all()]