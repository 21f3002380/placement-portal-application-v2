from flask import Blueprint, request, jsonify
from sqlalchemy import func
from backend.extensions import db
from backend.models import User, Student, Company, PlacementDrive, Application, Placement
from backend.auth import role_required
from backend.cache import cached, cache_clear_prefix

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@bp.get("/dashboard")
@role_required("admin")
def dashboard():
    return jsonify({
        "total_students": Student.query.count(),
        "total_companies": Company.query.count(),
        "total_drives": PlacementDrive.query.count(),
        "total_applications": Application.query.count(),
        "pending_companies": [c.to_dict() for c in
                              Company.query.filter_by(is_approved=False, is_blacklisted=False).all()],
        "pending_drives": [d.to_dict() for d in
                           PlacementDrive.query.filter_by(approval_status="Pending").all()],
        "recent_applications": [a.to_dict() for a in
                                Application.query.order_by(Application.applied_at.desc()).limit(10).all()],
    })


@bp.get("/companies")
@role_required("admin")
@cached(lambda: "admin:companies:" + request.args.get("q", "").strip().lower(), timeout=30)
def companies():
    q = request.args.get("q", "").strip()
    query = Company.query
    if q:
        query = query.filter(db.or_(
            Company.company_name.ilike(f"%{q}%"),
            Company.industry.ilike(f"%{q}%"),
        ))
    return [c.to_dict() for c in query.order_by(Company.id.desc()).all()]


@bp.post("/companies/<int:cid>/approve")
@role_required("admin")
def approve_company(cid):
    c = Company.query.get_or_404(cid)
    c.is_approved = True
    c.user.is_active = True          # fix: restore access on (re)approval
    db.session.commit()
    cache_clear_prefix("drives:")
    cache_clear_prefix("admin:companies:")
    cache_clear_prefix("student:companies:")
    return jsonify({"message": f"{c.company_name} approved."})


@bp.post("/companies/<int:cid>/reject")
@role_required("admin")
def reject_company(cid):
    c = Company.query.get_or_404(cid)
    c.is_approved = False
    db.session.commit()
    cache_clear_prefix("admin:companies:")
    cache_clear_prefix("student:companies:")
    return jsonify({"message": f"{c.company_name} rejected."})


@bp.post("/companies/<int:cid>/blacklist")
@role_required("admin")
def blacklist_company(cid):
    c = Company.query.get_or_404(cid)
    c.is_blacklisted = True
    c.user.is_active = False
    for d in c.drives:
        d.drive_status = "Closed"
        d.approval_status = "Rejected"
    db.session.commit()
    cache_clear_prefix("drives:")
    cache_clear_prefix("admin:companies:")
    cache_clear_prefix("student:companies:")
    return jsonify({"message": f"{c.company_name} blacklisted."})


@bp.post("/companies/<int:cid>/unblacklist")
@role_required("admin")
def unblacklist_company(cid):
    c = Company.query.get_or_404(cid)
    c.is_blacklisted = False
    c.user.is_active = True
    db.session.commit()
    cache_clear_prefix("admin:companies:")
    cache_clear_prefix("student:companies:")
    return jsonify({"message": f"{c.company_name} restored."})


@bp.get("/students")
@role_required("admin")
@cached(lambda: "admin:students:" + request.args.get("q", "").strip().lower(), timeout=30)
def students():
    q = request.args.get("q", "").strip()
    query = Student.query.join(User)
    if q:
        query = query.filter(db.or_(
            Student.name.ilike(f"%{q}%"),
            Student.roll_number.ilike(f"%{q}%"),
            User.email.ilike(f"%{q}%"),
        ))
    return [s.to_dict() for s in query.order_by(Student.id.desc()).all()]


@bp.post("/students/<int:sid>/blacklist")
@role_required("admin")
def blacklist_student(sid):
    s = Student.query.get_or_404(sid)
    s.is_blacklisted = True
    s.user.is_active = False
    db.session.commit()
    cache_clear_prefix("admin:students:")
    return jsonify({"message": f"{s.name} blacklisted."})


@bp.post("/students/<int:sid>/unblacklist")
@role_required("admin")
def unblacklist_student(sid):
    s = Student.query.get_or_404(sid)
    s.is_blacklisted = False
    s.user.is_active = True
    db.session.commit()
    cache_clear_prefix("admin:students:")
    return jsonify({"message": f"{s.name} restored."})


@bp.get("/drives")
@role_required("admin")
def drives():
    status = request.args.get("status", "all")
    query = PlacementDrive.query
    if status != "all":
        query = query.filter_by(approval_status=status)
    return jsonify([d.to_dict() for d in query.order_by(PlacementDrive.id.desc()).all()])


@bp.post("/drives/<int:did>/approve")
@role_required("admin")
def approve_drive(did):
    d = PlacementDrive.query.get_or_404(did)
    d.approval_status = "Approved"
    db.session.commit()
    cache_clear_prefix("drives:")
    return jsonify({"message": f'Drive "{d.title}" approved.'})


@bp.post("/drives/<int:did>/reject")
@role_required("admin")
def reject_drive(did):
    d = PlacementDrive.query.get_or_404(did)
    d.approval_status = "Rejected"
    db.session.commit()
    cache_clear_prefix("drives:")
    return jsonify({"message": f'Drive "{d.title}" rejected.'})

# Milestone 6: admin has unrestricted visibility
@bp.get("/applications")
@role_required("admin")
def applications():
    return jsonify([a.to_dict() for a in
                    Application.query.order_by(Application.applied_at.desc()).all()])


@bp.get("/stats")
@role_required("admin")
@cached(lambda: "admin:stats", timeout=30)
def stats():
    from datetime import datetime, timedelta
    from collections import Counter

    placed = db.session.query(func.count(func.distinct(Application.student_id)))\
        .filter(Application.application_status.in_(["Selected", "Placed"])).scalar()
    per_company = db.session.query(
        Company.company_name,
        func.count(Application.id),
        func.sum(db.case((Application.application_status.in_(["Selected", "Placed"]), 1), else_=0)),
    ).join(PlacementDrive, PlacementDrive.company_id == Company.id)\
     .join(Application, Application.drive_id == PlacementDrive.id)\
     .group_by(Company.id).all()

    status_rows = db.session.query(
        Application.application_status, func.count(Application.id)
    ).group_by(Application.application_status).all()
    status_distribution = {status: count for status, count in status_rows}

    now = datetime.now()
    buckets = []
    cursor = now.replace(day=1)
    for _ in range(6):
        buckets.append(cursor)
        cursor = (cursor - timedelta(days=1)).replace(day=1)
    buckets.reverse()
    monthly_placements = []
    for i, start in enumerate(buckets):
        end = buckets[i + 1] if i + 1 < len(buckets) else (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        count = Placement.query.filter(Placement.created_at >= start, Placement.created_at < end).count()
        monthly_placements.append({"month": start.strftime("%b %Y"), "count": count})

    skill_counter = Counter()
    drives_with_skills = PlacementDrive.query.filter(
        PlacementDrive.approval_status == "Approved",
        PlacementDrive.skills_required.isnot(None),
    ).all()
    for d in drives_with_skills:
        for skill in (d.skills_required or "").split(","):
            skill = skill.strip()
            if skill:
                skill_counter[skill] += 1
    skills_demand = [{"skill": s, "count": c} for s, c in skill_counter.most_common(8)]

    return {
        "total_students": Student.query.count(),
        "placed_students": placed or 0,
        "drives_open": PlacementDrive.query.filter_by(drive_status="Open", approval_status="Approved").count(),
        "drives_closed": PlacementDrive.query.filter_by(drive_status="Closed").count(),
        "company_stats": [
            {"company": name, "applications": total, "selected": int(sel or 0)}
            for name, total, sel in per_company
        ],
        "status_distribution": status_distribution,
        "monthly_placements": monthly_placements,
        "skills_demand": skills_demand,
    }