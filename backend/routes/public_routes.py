from flask import Blueprint, jsonify
from sqlalchemy import func
from backend.extensions import db
from backend.models import PlacementDrive, Student, Company, Application, Placement
from backend.cache import cached

bp = Blueprint("public", __name__, url_prefix="/api/public")


@bp.get("/drives")
@cached(lambda: "drives:public:approved_open", timeout=60)
def public_drives():
    drives = PlacementDrive.query.filter_by(
        approval_status="Approved", drive_status="Open"
    ).order_by(PlacementDrive.created_at.desc()).all()
    return [d.to_dict() for d in drives]


@bp.get("/stats")
@cached(lambda: "public:landing_stats", timeout=120)
def landing_stats():
    return {
        "total_companies": Company.query.filter_by(is_approved=True).count(),
        "total_students": Student.query.count(),
        "total_drives": PlacementDrive.query.filter_by(approval_status="Approved").count(),
        "total_placements": Placement.query.count(),
    }
