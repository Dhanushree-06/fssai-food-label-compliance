"""
History Blueprint Routes
AI-Based Food Label Compliance Verification Platform
"""

import os
import io
import csv
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, current_app
from app.models import db, ScanRecord

history_bp = Blueprint("history", __name__)


@history_bp.route("/history")
def history():
    """Displays audit history with search, status filters, and pagination/sorting."""
    search_query = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "").strip().upper()

    query = ScanRecord.query

    if search_query:
        query = query.filter(
            (ScanRecord.product_name.ilike(f"%{search_query}%")) |
            (ScanRecord.filename.ilike(f"%{search_query}%")) |
            (ScanRecord.original_ocr_text.ilike(f"%{search_query}%"))
        )

    if status_filter and status_filter in ["COMPLIANT", "NON_COMPLIANT"]:
        query = query.filter(ScanRecord.compliance_status == status_filter)

    scans = query.order_by(ScanRecord.created_at.desc()).all()

    return render_template(
        "history.html",
        scans=scans,
        search_query=search_query,
        status_filter=status_filter,
        total_scans=len(scans)
    )


@history_bp.route("/history/delete/<int:scan_id>", methods=["POST"])
def delete_scan(scan_id):
    """Deletes a scan record and its generated PDF / uploaded files."""
    scan = ScanRecord.query.get_or_404(scan_id)
    upload_dir = current_app.config["UPLOAD_FOLDER"]

    # Remove files if present
    for rel_path in [scan.image_path, scan.annotated_image_path, scan.preprocessed_image_path, scan.pdf_path]:
        if rel_path:
            full_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "static", rel_path
            )
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                except Exception as e:
                    print(f"[History Delete] Error removing file {full_path}: {e}")

    db.session.delete(scan)
    db.session.commit()
    flash(f"Scan record #{scan_id} ({scan.product_name}) was successfully deleted.", "success")
    return redirect(url_for("history.history"))


@history_bp.route("/history/export-csv")
def export_csv():
    """Exports full scan history to a downloadable CSV file."""
    scans = ScanRecord.query.order_by(ScanRecord.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Scan ID", "Product Name", "Audit Timestamp", "Evidence Coverage (%)",
        "Compliance Status", "OCR Engine", "Filename"
    ])

    for s in scans:
        writer.writerow([
            s.id,
            s.product_name,
            s.created_at.strftime("%Y-%m-%d %H:%M:%S") if s.created_at else "",
            round(s.overall_score, 1),
            s.compliance_status,
            s.ocr_engine,
            s.filename
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=fssai_compliance_audit_history.csv"}
    )
