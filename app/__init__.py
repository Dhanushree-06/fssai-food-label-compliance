"""
Flask Application Factory
AI-Based Food Label Compliance Verification Platform
"""

import os
from flask import Flask
from app.models import db


def create_app(test_config=None):
    """Initializes and configures the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "fssai_compliance.db")
    upload_dir = os.path.join(base_dir, "app", "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "fssai-verification-secret-key-2026"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URI", f"sqlite:///{db_path}"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=upload_dir,
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16 MB max upload
    )

    if test_config:
        app.config.update(test_config)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.verifier import verifier_bp
    from app.routes.history import history_bp
    from app.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(verifier_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # Create tables
    with app.app_context():
        db.create_all()
        from app.models import ScanRecord
        from app.services.fssai_rules import FIELD_DEFINITIONS, FSSAIRuleVerifier

        for scan in ScanRecord.query.all():
            field_statuses = {
                key: {"status": "MISSING"} for key in FIELD_DEFINITIONS
            }
            for field_result in scan.field_results:
                if field_result.field_key in field_statuses:
                    field_result.status = (
                        "PRESENT" if field_result.status == "PRESENT" else "MISSING"
                    )
                    field_statuses[field_result.field_key] = {"status": field_result.status}

            summary = FSSAIRuleVerifier.summarize_fields(field_statuses)
            scan.overall_score = summary["score"]
            scan.compliance_status = summary["compliance_status"]

        db.session.commit()

    return app
