"""
SQLAlchemy Database Models
AI-Based Food Label Compliance Verification Platform
"""

from datetime import datetime
import json
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class ScanRecord(db.Model):
    """Represents a food label verification scan event."""

    __tablename__ = "scan_records"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    annotated_image_path = db.Column(db.String(500), nullable=True)
    preprocessed_image_path = db.Column(db.String(500), nullable=True)
    product_name = db.Column(db.String(255), default="Packaged Food Product")
    food_category = db.Column(db.String(100), default="General Food")
    original_ocr_text = db.Column(db.Text, nullable=False)
    corrected_ocr_text = db.Column(db.Text, nullable=True)
    overall_score = db.Column(db.Float, default=0.0)
    compliance_status = db.Column(db.String(50), default="NON_COMPLIANT")
    ml_prediction = db.Column(db.String(50), default="NEEDS_REVIEW")
    ml_confidence = db.Column(db.Float, default=0.0)
    ocr_engine = db.Column(db.String(100), default="Unified Engine")
    pdf_path = db.Column(db.String(500), nullable=True)
    bounding_boxes_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    field_results = db.relationship(
        "FieldResult",
        backref="scan",
        cascade="all, delete-orphan",
        lazy=True
    )

    def to_dict(self):
        """Converts record to JSON-serializable dictionary."""
        boxes = []
        if self.bounding_boxes_json:
            try:
                boxes = json.loads(self.bounding_boxes_json)
            except Exception:
                boxes = []

        fields_dict = {f.field_key: f.to_dict() for f in self.field_results}

        return {
            "id": self.id,
            "filename": self.filename,
            "image_url": self.image_path.replace("\\", "/"),
            "annotated_image_url": self.annotated_image_path.replace("\\", "/") if self.annotated_image_path else None,
            "preprocessed_image_url": self.preprocessed_image_path.replace("\\", "/") if self.preprocessed_image_path else None,
            "product_name": self.product_name,
            "food_category": self.food_category,
            "original_ocr_text": self.original_ocr_text,
            "corrected_ocr_text": self.corrected_ocr_text or self.original_ocr_text,
            "overall_score": round(self.overall_score, 1),
            "compliance_status": self.compliance_status,
            "ocr_engine": self.ocr_engine,
            "pdf_url": self.pdf_path.replace("\\", "/") if self.pdf_path else None,
            "bounding_boxes": boxes,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "",
            "fields": fields_dict
        }


class FieldResult(db.Model):
    """Stores the evaluation finding for each of the 14 FSSAI fields."""

    __tablename__ = "field_results"

    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey("scan_records.id"), nullable=False)
    field_key = db.Column(db.String(50), nullable=False)
    field_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(30), nullable=False)  # PRESENT or MISSING
    confidence = db.Column(db.Float, default=0.0)
    evidence = db.Column(db.Text, nullable=True)
    rules_passed_json = db.Column(db.Text, nullable=True)
    recommendation = db.Column(db.Text, nullable=True)

    def to_dict(self):
        rules = []
        if self.rules_passed_json:
            try:
                rules = json.loads(self.rules_passed_json)
            except Exception:
                rules = []

        return {
            "field_key": self.field_key,
            "field_name": self.field_name,
            "status": "PRESENT" if self.status == "PRESENT" else "MISSING",
            "confidence": round(self.confidence, 2),
            "evidence": self.evidence,
            "rules_passed": rules,
            "recommendation": self.recommendation
        }
