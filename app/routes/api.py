"""
REST API Blueprint
AI-Based Food Label Compliance Verification Platform
"""

from flask import Blueprint, jsonify, request
from app.models import ScanRecord
from app.services.fssai_rules import FSSAIRuleVerifier

api_bp = Blueprint("api", __name__)


@api_bp.route("/verify_text", methods=["POST"])
def verify_text():
    """Programmatic API to verify raw label text against the 14 FSSAI fields."""
    data = request.get_json() or {}
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "No 'text' field provided in request body."}), 400

    rule_eval = FSSAIRuleVerifier.verify_all(text)

    return jsonify({
        "success": True,
        "score": rule_eval["score"],
        "compliance_status": rule_eval["compliance_status"],
        "status_description": rule_eval["status_description"],
        "fields": rule_eval["fields"]
    })


@api_bp.route("/scans", methods=["GET"])
def list_scans():
    """Returns recent audit scan summaries."""
    limit = min(int(request.args.get("limit", 20)), 100)
    scans = ScanRecord.query.order_by(ScanRecord.created_at.desc()).limit(limit).all()
    return jsonify([s.to_dict() for s in scans])
