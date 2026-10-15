"""
Integration Tests for Flask Web Application Routes
"""

import os
import json
from io import BytesIO
from app import create_app
from app.models import db, FieldResult, ScanRecord

SAMPLE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app", "static", "sample_images"
)


def get_test_app_and_client():
    """Helper to return an isolated testing app and client."""
    test_app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False
    })
    return test_app, test_app.test_client()


def post_sample_upload(client, filename):
    """Post a fixture image through the same upload flow used by the UI."""
    with open(os.path.join(SAMPLE_DIR, filename), "rb") as sample_file:
        image_data = sample_file.read()
    return client.post(
        "/verify",
        data={"label_image": (BytesIO(image_data), filename)},
        content_type="multipart/form-data"
    )


def test_home_page(client=None):
    """Verify landing page loads successfully."""
    if client is None:
        _, client = get_test_app_and_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"FSSAI Verifier" in response.data
    assert b"14 Checks" in response.data
    assert b"Download ZIP" not in response.data
    assert b"150 Samples" not in response.data
    assert b"Statutory Advisory" not in response.data
    assert b"Each field is marked PRESENT when supported by extracted evidence, otherwise MISSING." in response.data
    assert b"NEEDS REVIEW" not in response.data


def test_about_page(client=None):
    """Verify the regulations guide does not expose model or dataset metrics."""
    if client is None:
        _, client = get_test_app_and_client()
    response = client.get("/about")
    assert response.status_code == 200
    assert b"Food Label Regulations Guide" in response.data
    assert b"Ingredients" in response.data
    assert b"dataset" not in response.data.lower()
    assert b"confusion matrix" not in response.data.lower()


def test_upload_page_hides_preprocessing_controls(client=None):
    """The upload page shows neither preprocessing controls nor demo samples."""
    if client is None:
        _, client = get_test_app_and_client()
    response = client.get("/verify")
    assert response.status_code == 200
    assert b"OpenCV Image Preprocessing Controls" not in response.data
    assert b"Text Deskewing" not in response.data
    assert b"Compliant Demo" not in response.data
    assert b"Pre-loaded Sample" not in response.data
    assert b"sampleChoiceInput" not in response.data
    assert b"Browse Files" in response.data


def test_verify_get_page(client=None):
    """Verify check FSSAI label upload page loads without demo selectors."""
    if client is None:
        _, client = get_test_app_and_client()
    response = client.get("/verify")
    assert response.status_code == 200
    assert b"Upload a packaged food label image" in response.data


def test_existing_scan_refreshes_ocr_nutrition_and_mrp():
    """Previously saved scans use updated OCR parsing rules when reopened."""
    app_instance, client = get_test_app_and_client()
    ocr_text = (
        "Nutritional Information\nIngredients:\nPotatoes, Vegetable Oil\nPer 100 g\n"
        "Energy\n536 kcal\nProtein\n6.5 g\nCarbohydrate\n50.2 g\n"
        "Total Sugars\n1.2 g\nTotal Fat\n36.8 g\nSodium\n410mg\n"
        "Manufactured & Packed by: GoodBite Foods\n"
        "MRP (incl. of all taxes):\nBengaluru - 560058, Karnataka, India.\n#40.00"
    )
    with app_instance.app_context():
        scan = ScanRecord(
            filename="old-scan.jpg",
            image_path="uploads/old-scan.jpg",
            original_ocr_text=ocr_text,
            corrected_ocr_text=ocr_text,
        )
        db.session.add(scan)
        db.session.flush()
        for field_key in ("nutrition", "mrp"):
            db.session.add(FieldResult(
                scan_id=scan.id,
                field_key=field_key,
                field_name=field_key,
                status="MISSING",
                confidence=0.0,
                evidence="Not detected",
                rules_passed_json="[]",
                recommendation="Review label",
            ))
        scan_id = scan.id
        db.session.commit()

    response = client.get(f"/verify/{scan_id}")
    assert response.status_code == 200
    assert b"Nutrition heading and numeric nutrient values detected." in response.data
    assert b"MRP declared: Rs. 40.00" in response.data
    with app_instance.app_context():
        scan = ScanRecord.query.get(scan_id)
        assert {field.field_key: field.status for field in scan.field_results} == {
            "nutrition": "PRESENT",
            "mrp": "PRESENT",
        }


def test_verify_rejects_hidden_sample_selection(client=None):
    """The upload route no longer accepts sample selection in place of an upload."""
    app_instance = None
    if client is None:
        app_instance, client = get_test_app_and_client()
    response = client.post(
        "/verify",
        data={"sample_choice": "sample_snack_pack.png"},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Please upload a food label image to continue." in response.data
    if app_instance:
        with app_instance.app_context():
            assert ScanRecord.query.count() == 0


def test_verify_post_uploaded_image(client=None):
    """Verify the label upload workflow using a test fixture image."""
    if client is None:
        _, client = get_test_app_and_client()
    response = post_sample_upload(client, "sample_snack_pack.png")
    response = client.get(response.location, follow_redirects=True)

    assert response.status_code == 200
    assert b"Audit Results" in response.data
    assert b"Evidence Coverage" in response.data
    assert b"14 FSSAI Label Reference Checks" in response.data
    assert b"Enhanced Image" in response.data
    assert b"View at original size" in response.data
    assert b"NEEDS REVIEW" not in response.data
    assert b">INVALID<" not in response.data
    assert b"Machine Learning" not in response.data


def test_recheck_api_workflow(client=None):
    """Verify interactive OCR text re-evaluation API endpoint."""
    app_instance, client = get_test_app_and_client()
    
    # First create a scan
    response = post_sample_upload(client, "sample_snack_pack.png")
    client.get(response.location, follow_redirects=True)
    
    # Get scan record ID
    with app_instance.app_context():
        scan = ScanRecord.query.first()
        assert scan is not None
        scan_id = scan.id

    # Call /api/recheck/<scan_id>
    updated_ocr = (
        "CRISP KRAFT POTATO CHIPS. "
        "Ingredients: Potatoes (64%), Palmolein Oil, Salt, Spices. "
        "Nutrition per 100g: Energy 540 kcal, Protein 6.8g, Fat 34g, Sodium 780mg. "
        "Vegetarian Green Dot Symbol. "
        "Manufactured by: Crisp Kraft Snacks, GIDC, Sanand, Gujarat - 382110. "
        "Customer Care: 1800-200-5544, care@crispkraft.in. "
        "Net Quantity: 115 g. MRP: Rs. 40.00 incl. of all taxes. "
        "FSSAI Lic. No. 10017042001923. Batch No: SPK8812. "
        "Date of Pkg: 15/09/2026. Best Before 4 months. "
        "Store in a cool dry place. Country of Origin: India."
    )

    recheck_resp = client.post(
        f"/api/recheck/{scan_id}",
        data=json.dumps({"ocr_text": updated_ocr}),
        content_type="application/json"
    )

    assert recheck_resp.status_code == 200
    res_json = recheck_resp.get_json()
    assert res_json["success"] is True
    assert "scan" in res_json
    assert res_json["scan"]["overall_score"] >= 80.0
    assert {field["status"] for field in res_json["scan"]["fields"].values()} <= {
        "PRESENT", "MISSING"
    }
    assert res_json["scan"]["fields"]["veg_nonveg"]["status"] == "PRESENT"
    assert "ml_prediction" not in res_json["scan"]
    assert "ml_confidence" not in res_json["scan"]


def test_history_and_export(client=None):
    """Verify history page, search filter, and CSV export."""
    app_instance, client = get_test_app_and_client()
    
    # Create sample scan
    response = post_sample_upload(client, "sample_mango_juice.png")
    client.get(response.location, follow_redirects=True)

    # History view
    hist_resp = client.get("/history")
    assert hist_resp.status_code == 200
    assert b"Audit Verification History" in hist_resp.data

    # CSV Export
    csv_resp = client.get("/history/export-csv")
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.content_type
    assert b"Evidence Coverage (%)" in csv_resp.data
    assert b"ML Prediction" not in csv_resp.data


def test_api_verify_text(client=None):
    """Verify standalone REST API text verification."""
    if client is None:
        _, client = get_test_app_and_client()
    payload = {
        "text": (
            "Whole Wheat Bread. Ingredients: Flour, Water, Yeast. "
            "Nutrition per 100g: Energy 250 kcal, Protein 8g, Carbs 50g, Fat 2g, Sodium 400mg. "
            "Green Vegetarian Logo. Mfd by: Baker Co, Sector 10, Delhi - 110001. "
            "Customer Helpline: 1800-111-222, info@baker.com. "
            "Net Wt: 400 g. MRP Rs 45.00 incl of taxes. "
            "FSSAI Lic. No. 10019064001234. Batch: B101. Mfg: 10/10/2026. Best Before: 15/10/2026. "
            "Store in a cool dry place. Product of India."
        )
    }
    resp = client.post("/api/verify_text", data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["compliance_status"] == "NON_COMPLIANT"
    assert {field["status"] for field in data["fields"].values()} <= {
        "PRESENT", "MISSING"
    }
    assert data["score"] >= 85.0
    assert "ml_prediction" not in data
    assert "ml_confidence" not in data
    assert client.get("/api/metrics").status_code == 404


def test_download_zip_route(client=None):
    """Verify the project ZIP download route has been removed."""
    if client is None:
        _, client = get_test_app_and_client()
    resp = client.get("/download-zip")
    assert resp.status_code == 404
