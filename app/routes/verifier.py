"""
Verifier Blueprint Routes
AI-Based Food Label Compliance Verification Platform
"""

import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, current_app
)
from app.models import db, ScanRecord, FieldResult
from app.services.image_processing import ImagePreprocessor
from app.services.ocr_engine import OCREngine
from app.services.fssai_rules import FSSAIRuleVerifier, FIELD_DEFINITIONS
from app.services.pdf_generator import PDFReportGenerator

verifier_bp = Blueprint("verifier", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _refresh_ocr_field_results(scan):
    """Refresh nutrition and MRP findings for scans saved with older parsing rules."""
    text = scan.corrected_ocr_text or scan.original_ocr_text
    refreshed_fields = FSSAIRuleVerifier.verify_all(text)["fields"]
    changed = False

    for field_result in scan.field_results:
        if field_result.field_key not in {"nutrition", "mrp"}:
            continue

        result = refreshed_fields[field_result.field_key]
        rules_passed_json = json.dumps(result.get("rules_passed", []))
        if (
            field_result.status != result["status"]
            or field_result.confidence != result["confidence"]
            or field_result.evidence != result["evidence"]
            or field_result.rules_passed_json != rules_passed_json
            or field_result.recommendation != result["recommendation"]
        ):
            field_result.status = result["status"]
            field_result.confidence = result["confidence"]
            field_result.evidence = result["evidence"]
            field_result.rules_passed_json = rules_passed_json
            field_result.recommendation = result["recommendation"]
            changed = True

    if changed:
        fields = {item.field_key: item.to_dict() for item in scan.field_results}
        summary = FSSAIRuleVerifier.summarize_fields(fields)
        scan.overall_score = summary["score"]
        scan.compliance_status = summary["compliance_status"]
        db.session.commit()


@verifier_bp.route("/verify", methods=["GET", "POST"])
def verify():
    """Upload a food label image for compliance screening."""
    if request.method == "POST":
        uploaded_file = request.files.get("label_image")

        upload_dir = current_app.config["UPLOAD_FOLDER"]
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

        if not uploaded_file or uploaded_file.filename == "":
            flash("Please upload a food label image to continue.", "warning")
            return redirect(url_for("verifier.verify"))
        if not allowed_file(uploaded_file.filename):
            flash("Invalid file format. Please upload PNG, JPG, JPEG, or WEBP.", "danger")
            return redirect(url_for("verifier.verify"))

        clean_name = secure_filename(uploaded_file.filename)
        target_filename = f"scan_{timestamp_str}_{clean_name}"
        target_path = os.path.join(upload_dir, target_filename)
        uploaded_file.save(target_path)
        display_name = clean_name.rsplit(".", 1)[0].replace("_", " ").title()

        # Preprocess automatically; users do not need to tune image controls.
        try:
            preproc_res = ImagePreprocessor.preprocess_pipeline(target_path)
            preprocessed_filename = preproc_res["processed_filename"]
        except Exception as e:
            print(f"[Verifier] Preprocessing error: {e}")
            preprocessed_filename = None

        # Detect the statutory veg/non-veg symbol from the original image.
        cv_symbol = ImagePreprocessor.detect_veg_nonveg_symbol(target_path)

        # Try the original image first, then the automatically enhanced image.
        ocr_result = OCREngine.extract_text(target_path, preprocessed_path=(
            os.path.join(upload_dir, preprocessed_filename) if preprocessed_filename else None
        ))
        extracted_text = ocr_result["full_text"]
        if not extracted_text.strip():
            paths_to_clean = [target_path]
            if preprocessed_filename:
                paths_to_clean.append(os.path.join(upload_dir, preprocessed_filename))
            for path in paths_to_clean:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except OSError as error:
                    print(f"[Verifier] Could not remove unreadable scan file {path}: {error}")
            flash(
                "No readable text could be extracted. Upload a clearer, higher-resolution image and ensure the local OCR engine is available.",
                "danger"
            )
            return redirect(url_for("verifier.verify"))
        bounding_boxes = ocr_result["bounding_boxes"]
        ocr_engine_name = ocr_result["engine_used"]

        # Step 4: Draw Annotated Bounding Boxes
        annotated_filename = f"annotated_{target_filename}"
        annotated_path = os.path.join(upload_dir, annotated_filename)
        ImagePreprocessor.draw_annotated_image(
            ocr_result.get("image_path_used", target_path),
            bounding_boxes,
            annotated_path
        )

        # Step 5: 14 FSSAI Rules Verification
        rule_eval = FSSAIRuleVerifier.verify_all(extracted_text, cv_symbol)

        # Step 6: Save Scan Record to Database
        scan = ScanRecord(
            filename=target_filename,
            image_path=f"uploads/{target_filename}",
            annotated_image_path=f"uploads/{annotated_filename}",
            preprocessed_image_path=f"uploads/{preprocessed_filename}" if preprocessed_filename else None,
            product_name=display_name,
            original_ocr_text=extracted_text,
            corrected_ocr_text=extracted_text,
            overall_score=rule_eval["score"],
            compliance_status=rule_eval["compliance_status"],
            ocr_engine=ocr_engine_name,
            bounding_boxes_json=json.dumps(bounding_boxes)
        )
        db.session.add(scan)
        db.session.flush()  # obtain scan.id

        # Save individual field results
        for f_key, f_data in rule_eval["fields"].items():
            field_def = FIELD_DEFINITIONS.get(f_key, {})
            fr = FieldResult(
                scan_id=scan.id,
                field_key=f_key,
                field_name=field_def.get("title", f_key.replace("_", " ").title()),
                status=f_data["status"],
                confidence=f_data["confidence"],
                evidence=f_data["evidence"],
                rules_passed_json=json.dumps(f_data.get("rules_passed", [])),
                recommendation=f_data["recommendation"]
            )
            db.session.add(fr)

        # Step 8: Generate ReportLab PDF
        pdf_filename = f"report_scan_{scan.id}.pdf"
        pdf_path = os.path.join(upload_dir, pdf_filename)
        pdf_data = {
            "id": scan.id,
            "product_name": scan.product_name,
            "date": scan.created_at.strftime("%Y-%m-%d %H:%M"),
            "score": rule_eval["score"],
            "compliance_status": rule_eval["compliance_status"],
            "ocr_engine": ocr_engine_name,
            "status_counts": rule_eval["status_counts"],
            "fields": rule_eval["fields"]
        }
        PDFReportGenerator.generate_report(pdf_data, pdf_path)
        scan.pdf_path = f"uploads/{pdf_filename}"

        db.session.commit()
        return redirect(url_for("verifier.view_scan", scan_id=scan.id))

    # GET request: render verify form
    return render_template("verify.html", fields_definitions=FIELD_DEFINITIONS)


@verifier_bp.route("/verify/<int:scan_id>")
def view_scan(scan_id):
    """Interactive compliance audit dashboard for a specific scan."""
    scan = ScanRecord.query.get_or_404(scan_id)
    _refresh_ocr_field_results(scan)
    scan_dict = scan.to_dict()
    scan_dict.update(FSSAIRuleVerifier.summarize_fields(scan_dict["fields"]))
    return render_template(
        "verify_results.html",
        scan=scan,
        scan_dict=scan_dict,
        fields_definitions=FIELD_DEFINITIONS
    )


@verifier_bp.route("/api/recheck/<int:scan_id>", methods=["POST"])
def recheck_scan(scan_id):
    """
    Re-evaluates the 14 FSSAI reference checks using corrected OCR text.
    Updates the database and regenerates the PDF report.
    """
    scan = ScanRecord.query.get_or_404(scan_id)
    data = request.get_json() or {}
    new_text = data.get("ocr_text", "").strip()

    if not new_text:
        return jsonify({"success": False, "error": "No OCR text provided."}), 400

    # Re-verify with 14 rules
    image_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        os.path.basename(scan.filename)
    )
    cv_symbol = (
        ImagePreprocessor.detect_veg_nonveg_symbol(image_path)
        if os.path.exists(image_path) else None
    )
    rule_eval = FSSAIRuleVerifier.verify_all(new_text, cv_symbol)

    # Update database record
    scan.corrected_ocr_text = new_text
    scan.overall_score = rule_eval["score"]
    scan.compliance_status = rule_eval["compliance_status"]

    # Update FieldResult entities
    for fr in scan.field_results:
        if fr.field_key in rule_eval["fields"]:
            f_data = rule_eval["fields"][fr.field_key]
            fr.status = f_data["status"]
            fr.confidence = f_data["confidence"]
            fr.evidence = f_data["evidence"]
            fr.rules_passed_json = json.dumps(f_data.get("rules_passed", []))
            fr.recommendation = f_data["recommendation"]

    # Re-generate PDF report
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    pdf_filename = f"report_scan_{scan.id}.pdf"
    pdf_path = os.path.join(upload_dir, pdf_filename)
    pdf_data = {
        "id": scan.id,
        "product_name": scan.product_name,
        "date": scan.created_at.strftime("%Y-%m-%d %H:%M"),
        "score": rule_eval["score"],
        "compliance_status": rule_eval["compliance_status"],
        "ocr_engine": scan.ocr_engine,
        "status_counts": rule_eval["status_counts"],
        "fields": rule_eval["fields"]
    }
    PDFReportGenerator.generate_report(pdf_data, pdf_path)
    scan.pdf_path = f"uploads/{pdf_filename}"

    db.session.commit()

    return jsonify({
        "success": True,
        "scan": scan.to_dict(),
        "rule_eval": rule_eval,
        "pdf_url": url_for("verifier.download_pdf", scan_id=scan.id)
    })


@verifier_bp.route("/download-pdf/<int:scan_id>")
def download_pdf(scan_id):
    """Serves the generated ReportLab PDF audit report."""
    scan = ScanRecord.query.get_or_404(scan_id)
    _refresh_ocr_field_results(scan)
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    pdf_filename = f"report_scan_{scan.id}.pdf"
    pdf_path = os.path.join(upload_dir, pdf_filename)

    fields_dict = {f.field_key: f.to_dict() for f in scan.field_results}
    summary = FSSAIRuleVerifier.summarize_fields(fields_dict)

    pdf_data = {
        "id": scan.id,
        "product_name": scan.product_name,
        "date": scan.created_at.strftime("%Y-%m-%d %H:%M"),
        "score": summary["score"],
        "compliance_status": summary["compliance_status"],
        "ocr_engine": scan.ocr_engine,
        "status_counts": summary["status_counts"],
        "fields": fields_dict
    }
    PDFReportGenerator.generate_report(pdf_data, pdf_path)

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"FSSAI_Audit_Report_Scan_{scan.id}.pdf",
        mimetype="application/pdf"
    )
