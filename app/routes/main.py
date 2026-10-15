"""
Main Blueprint Routes (Home and Regulations Guide)
AI-Based Food Label Compliance Verification Platform
"""

from flask import Blueprint, render_template
from app.models import ScanRecord
from app.services.fssai_rules import FIELD_DEFINITIONS

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Platform landing page with summary stats, regulations overview, and recent audits."""
    total_scans = ScanRecord.query.count()
    compliant_scans = ScanRecord.query.filter_by(compliance_status="COMPLIANT").count()
    recent_scans = ScanRecord.query.order_by(ScanRecord.created_at.desc()).limit(5).all()

    return render_template(
        "index.html",
        total_scans=total_scans,
        compliant_scans=compliant_scans,
        recent_scans=recent_scans,
        fields_definitions=FIELD_DEFINITIONS
    )


@main_bp.route("/about")
def about():
    """Regulatory guide for the 14 label checks."""
    return render_template("about.html", fields_definitions=FIELD_DEFINITIONS)
