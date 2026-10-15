# FSSAI Food Label Screening Platform

An enterprise-grade, full-stack Flask web application engineered to audit packaged food labels against the **14 statutory labelling requirements** under the **Food Safety and Standards Authority of India (FSSAI) Labelling and Display Regulations, 2020**.

---

## Key Highlights & Core Capabilities

1. **Computer Vision & Image Preprocessing (OpenCV)**:
   - Automated text deskewing via contour minimum-area bounding rectangles.
   - Bilateral filter denoising to remove paper texture while preserving sharp character edges.
   - CLAHE (Contrast Limited Adaptive Histogram Equalization).
   - Adaptive Gaussian thresholding and Otsu binarization for enhanced OCR accuracy.
   - HSV color mask contour detection to isolate FSSAI statutory Vegetarian (Green dot in square) and Non-Vegetarian (Brown triangle in square) logos.

2. **Local OCR Pipeline**:
   - Uses RapidOCR/ONNX Runtime by default, with PaddleOCR and EasyOCR as optional alternatives.
   - Reads the uploaded image itself and can compare the original with an automatically enhanced copy.
   - Does not infer label contents from sample filenames. If no OCR engine can read text, the scan is stopped rather than returning fabricated findings.
   - Generates ordered text lines, bounding boxes, and OCR confidence ratings.
   - Live in-browser editable OCR interface allowing food auditors to correct misread characters and dynamically recalculate compliance without page refresh.

3. **Conservative Evidence-Based Screening**:
   - Calculates a weighted evidence-coverage score from the 14 field findings.
   - Marks a scan `COMPLIANT` only when all 14 checks have confirmed evidence.
   - Displays only `PRESENT` or `MISSING` for each field. `MISSING` means evidence was not detected in OCR and should be checked against the original image.
   - Marks a scan `COMPLIANT` only when all 14 checks have confirmed evidence; otherwise it is `NON_COMPLIANT`.

4. **14 FSSAI Label Reference Checks**:
   - Evaluates each field against statutory provisions and displays only `PRESENT` or `MISSING`.
   - Requires specific evidence for each check (for example, a 14-digit FSSAI licence number or net quantity with a unit); unsupported declarations are marked `MISSING`.
   - 14 statutory fields verified:
     1. Name of Food (Regulation 5(1))
     2. List of Ingredients (Regulation 5(2))
     3. Nutritional Information per 100g/serving (Regulation 5(3))
     4. Veg / Non-Veg Symbol (Regulation 5(4))
     5. Declaration of Food Additives & INS codes (Regulation 5(5))
     6. Manufacturer Name & Complete Address with PIN code (Regulation 5(6))
     7. Customer Care Helpline & Email (Regulation 5(7))
     8. Net Quantity in metric units (Regulation 5(8))
     9. Retail Sale Price (MRP incl. of all taxes) (Regulation 5(9))
     10. FSSAI Logo & 14-Digit Licence Number (Regulation 5(10))
     11. Lot / Code / Batch Identification (Regulation 5(11))
     12. Date Marking: Mfg/Packaging & Expiry/Best Before (Regulation 5(12))
     13. Instructions for Use & Storage Conditions (Regulation 5(13))
     14. Country of Origin (Regulation 5(14))

5. **Downloadable Audit Reports & Persistence**:
   - Automated branded PDF audit reports generated with **ReportLab**.
   - SQLite database managed by SQLAlchemy to persist scan history, scores, and field findings.
   - Comprehensive audit log with search, filtering by compliance posture, CSV export, and deletion.

---

## Windows CMD Setup & Run Instructions

Follow these exact steps from a Windows Command Prompt (`cmd.exe`):

### 1. Open Windows CMD and Navigate to the Project Directory
```cmd
cd /d "C:\Users\Dhanushree\.gemini\antigravity\scratch\fssai_compliance_platform"
```

### 2. (Optional) Create and Activate a Virtual Environment
```cmd
python -m venv venv
call venv\Scripts\activate.bat
```

### 3. Install Dependencies
```cmd
python -m pip install -r requirements.txt
```

*(RapidOCR and its local ONNX Runtime models are installed with the requirements. PaddleOCR/EasyOCR can optionally be installed as alternate OCR engines.)*

### 4. Generate Sample Label Images
```cmd
python generate_samples.py
```

### 5. Run the Test Suite
```cmd
python -m pytest tests/ -v
```

### 6. Start the Web Application
```cmd
python run.py
```

Open your browser and navigate to:
**`http://127.0.0.1:5000`**

---

## Project Folder Structure

```
fssai_compliance_platform/
├── app/
│   ├── __init__.py                # Flask application factory
│   ├── models.py                  # ScanRecord & FieldResult SQLAlchemy models
│   ├── routes/
│   │   ├── main.py                # Home ('/') and regulations guide ('/about')
│   │   ├── verifier.py            # Upload, verification dashboard, and interactive recheck API
│   │   ├── history.py             # Audit history, filtering, deletion, and CSV export
│   │   └── api.py                 # Text verification and scan-list API
│   ├── services/
│   │   ├── image_processing.py    # OpenCV filters, deskewing, binarization, symbol detection
│   │   ├── ocr_engine.py          # Unified OCR (PaddleOCR -> EasyOCR -> Fallback)
│   │   ├── ml_classifier.py       # Internal development utility
│   │   ├── fssai_rules.py         # 14 FSSAI fields evidence-based rule verification engine
│   │   └── pdf_generator.py       # ReportLab PDF audit report generator
│   ├── templates/
│   │   ├── base.html              # Base layout with navbar and theme toggler
│   │   ├── index.html             # Landing page with live stats and pipeline overview
│   │   ├── verify.html            # Food-label image upload dropzone
│   │   ├── verify_results.html    # Interactive audit dashboard, OCR editor, and charts
│   │   ├── history.html           # Searchable scan history log
│   │   └── about.html             # 14-field regulations guide
│   └── static/
│       ├── css/style.css          # Modern custom CSS styling
│       ├── sample_images/         # 4 pre-loaded food label sample images
│       └── uploads/               # Uploaded images and generated PDF reports
├── data/                          # Internal development artifacts; not used to determine screening status
├── tests/
│   ├── test_fssai_rules.py        # Unit tests for all 14 mandatory field validators
│   ├── test_image_processing.py   # Unit tests for OpenCV filters, deskewing, and contours
│   ├── test_ml_model.py           # Internal development-asset tests
│   └── test_routes.py             # Integration tests for Flask routes, uploads, and DB
├── train_model.py                 # Internal model-training utility
├── generate_samples.py            # Generates realistic food label sample images
├── create_zip.py                  # Project packaging utility
├── requirements.txt               # Dependencies
├── .env.example                   # Environment configuration example
├── README.md                      # Complete documentation
└── run.py                         # Application entrypoint
```

---

## Statutory Legal & Regulatory Disclaimer

> [!WARNING]
> This platform is an image-processing and rule-based assistive tool designed to aid food business operators, researchers, label designers, and consumers in preliminary screening.
>
> 1. It **does NOT constitute official certification, endorsement, or approval** by the Food Safety and Standards Authority of India (FSSAI) or any government agency.
> 2. `MISSING` means the declaration was not detected in the extracted evidence; check the original image because OCR can miss or misread text.
> 3. Definitive legal compliance determinations remain exclusively governed by statutory laboratory testing and official physical inspections under the Food Safety and Standards Act, 2006.
