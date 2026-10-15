"""
Unit Tests for 14 FSSAI Mandatory Field Validators
"""

from app.services.fssai_rules import FSSAIRuleVerifier, FIELD_DEFINITIONS



def test_field_definitions_count():
    """Verify that all 14 FSSAI fields are defined."""
    assert len(FIELD_DEFINITIONS) == 14
    total_weight = sum(f["weight"] for f in FIELD_DEFINITIONS.values())
    assert total_weight == 100


def test_food_name_validation():
    """Test Food Name field validation."""
    # Positive
    res = FSSAIRuleVerifier._verify_food_name("WHOLE WHEAT BREAD. Freshly baked.")
    assert res["status"] in ["PRESENT", "NEEDS_REVIEW"]

    # Country-of-origin wording must not be treated as the food name.
    res_origin = FSSAIRuleVerifier._verify_food_name("Product of India.")
    assert res_origin["status"] != "PRESENT"

    # Negative
    res_empty = FSSAIRuleVerifier._verify_food_name("")
    assert res_empty["status"] == "MISSING"


def test_ingredients_validation():
    """Test List of Ingredients validation."""
    # Positive: contains list
    text = "Ingredients: Whole Wheat Flour (60%), Water, Sugar, Edible Vegetable Oil, Salt."
    res = FSSAIRuleVerifier._verify_ingredients(text)
    assert res["status"] == "PRESENT"

    # The ingredient section must stop before a following nutrition section.
    text_with_nutrition = "Ingredients: Flour, Water. Nutrition per 100g: Energy 200 kcal."
    res_sections = FSSAIRuleVerifier._verify_ingredients(text_with_nutrition)
    assert "Nutrition" not in res_sections["evidence"]

    # OCR may split words or omit punctuation in a section heading.
    text_ocr = "Ingredie nts Potatoes (64%), Palm oil, Salt. NUTRI TIONAL INFORMATION Energy 250 kcal."
    res_ocr = FSSAIRuleVerifier.verify_all(text_ocr)["fields"]["ingredients"]
    assert res_ocr["status"] == "PRESENT"
    assert "Nutrition" not in res_ocr["evidence"]

    # OCR can flatten a visual ingredient list and omit its separators.
    text_flattened = (
        "INGREDIENTS\nPOTATOES VEGETABLE OIL SALT\n"
        "NUTRITIONAL INFORMATION Energy 250 kcal."
    )
    res_flattened = FSSAIRuleVerifier.verify_all(text_flattened)["fields"]["ingredients"]
    assert res_flattened["status"] == "PRESENT"
    assert "POTATOES VEGETABLE OIL SALT" in res_flattened["evidence"]

    # Invalid: keyword without list
    text_invalid = "Ingredients:"
    res_inv = FSSAIRuleVerifier._verify_ingredients(text_invalid)
    assert res_inv["status"] in ["INVALID", "NEEDS_REVIEW"]

    res_not_declared = FSSAIRuleVerifier.verify_all(
        "Ingredients: Not declared on pack."
    )["fields"]["ingredients"]
    assert res_not_declared["status"] == "MISSING"

    res_placeholder = FSSAIRuleVerifier._verify_ingredients(
        "Ingredients: Not declared on pack."
    )
    assert res_placeholder["status"] == "INVALID"

    # Missing
    res_missing = FSSAIRuleVerifier._verify_ingredients("Pure milk product without text.")
    assert res_missing["status"] == "MISSING"


def test_nutrition_validation():
    """Test Nutritional Information validation."""
    # Positive requires a numeric value and unit for each checked nutrient.
    text = (
        "Nutritional Information per 100g: Energy 450 kcal, Protein 8.5g, "
        "Carbohydrates 65g, Total Sugars 4g, Added Sugars 2g, Total Fat 18g, "
        "Saturated Fat 5g, Trans Fat 0g, Sodium 420mg."
    )
    res = FSSAIRuleVerifier._verify_nutrition(text)
    assert res["status"] == "PRESENT"

    # A readable table is present even if not every nutrient value was found.
    text_partial = "Nutritional Information: Energy 100 kcal, Protein 2g."
    res_part = FSSAIRuleVerifier._verify_nutrition(text_partial)
    assert res_part["status"] == "PRESENT"

    complete_without_basis = (
        "Nutritional Information: Energy 450 kcal, Protein 8.5g, Carbohydrates 65g, "
        "Total Sugars 4g, Added Sugars 2g, Total Fat 18g, Saturated Fat 5g, "
        "Trans Fat 0g, Sodium 420mg."
    )
    assert FSSAIRuleVerifier._verify_nutrition(complete_without_basis)["status"] == "PRESENT"

    # OCR may place ingredients between the heading and a vertically aligned table.
    ocr_table = (
        "Nutritional Information\nIngredients:\nPotatoes, Vegetable Oil\nPer 100 g\n"
        "Energy\n536 kcal\nProtein\n6.5 g\nCarbohydrate\n50.2 g\n"
        "Total Sugars\n1.2 g\nTotal Fat\n36.8 g\nSodium\n410mg\n"
        "Manufactured & Packed by: GoodBite Foods"
    )
    assert FSSAIRuleVerifier._verify_nutrition(ocr_table)["status"] == "PRESENT"

    # No numeric nutrition table is treated as missing.
    text_empty_nut = "Nutritional Information: high quality natural nutrients."
    res_inv = FSSAIRuleVerifier._verify_nutrition(text_empty_nut)
    assert res_inv["status"] == "MISSING"

    # Missing
    res_miss = FSSAIRuleVerifier._verify_nutrition("No data printed.")
    assert res_miss["status"] == "MISSING"

    # Descriptive mentions in a warning are not nutrient values.
    text_warning = (
        "Nutrition information missing: energy, protein, carbohydrates, sugars, "
        "fat and sodium."
    )
    assert FSSAIRuleVerifier._verify_nutrition(text_warning)["status"] == "MISSING"


def test_veg_nonveg_validation():
    """Test Veg / Non-Veg Symbol validation."""
    # Positive text
    text_veg = "Vegetarian Logo (Green Circle in Square) Declared."
    res = FSSAIRuleVerifier._verify_veg_nonveg(
        text_veg,
        {"detected": True, "type": "VEGETARIAN"}
    )
    assert res["status"] == "PRESENT"

    # OCR text cannot confirm that the physical statutory symbol is printed.
    res_text_only = FSSAIRuleVerifier._verify_veg_nonveg("Vegetarian food product.")
    assert res_text_only["status"] == "NEEDS_REVIEW"

    # Conflicting / Invalid
    text_conflict = "100% Vegetarian product. Ingredients: Wheat flour, Egg Solids, Salt."
    res_conf = FSSAIRuleVerifier._verify_veg_nonveg(text_conflict)
    assert res_conf["status"] == "INVALID"

    # Text-only checks cannot conclude that a visual symbol is absent.
    res_miss = FSSAIRuleVerifier._verify_veg_nonveg("Flour, sugar, butter.")
    assert res_miss["status"] == "NEEDS_REVIEW"

    res_absent = FSSAIRuleVerifier._verify_veg_nonveg(
        "Violation: Mandatory green veg dot or brown non-veg symbol is ABSENT!"
    )
    assert res_absent["status"] == "INVALID"


def test_additives_validation():
    """Test Food Additives INS numbers validation."""
    text = "Contains Preservative (INS 282) and Acidity Regulator (INS 330)."
    res = FSSAIRuleVerifier._verify_additives(text)
    assert res["status"] == "PRESENT"


def test_manufacturer_validation():
    """Test Manufacturer Name & Address validation."""
    # Positive: complete address with PIN
    text = "Manufactured by: Surya Bakers Pvt Ltd, Plot 45, Sector 18, Gurugram, Haryana - 122015."
    res = FSSAIRuleVerifier._verify_manufacturer(text)
    assert res["status"] == "PRESENT"

    # Needs review / incomplete: no PIN or full address
    text_inc = "Manufactured by: Sweet Bakers"
    res_inc = FSSAIRuleVerifier._verify_manufacturer(text_inc)
    assert res_inc["status"] in ["NEEDS_REVIEW", "INVALID"]

    text_company_suffix = "Mfd by: Baker Co, Sector 10, Delhi - 110001"
    assert FSSAIRuleVerifier._verify_manufacturer(text_company_suffix)["status"] == "PRESENT"


def test_customer_care_validation():
    """Test Customer Care contact validation."""
    # Positive
    text = "Customer Care Helpline: 1800-200-8899, Email: care@suryabakers.com"
    res = FSSAIRuleVerifier._verify_customer_care(text)
    assert res["status"] == "PRESENT"

    # Invalid: keyword with 'None'
    text_none = "Customer Care: None"
    res_none = FSSAIRuleVerifier._verify_customer_care(text_none)
    assert res_none["status"] == "INVALID"

    # Contact details without a customer-care heading are not proof of support.
    res_unrelated = FSSAIRuleVerifier._verify_customer_care(
        "Manufactured by Baker Foods, support@baker.com"
    )
    assert res_unrelated["status"] == "NEEDS_REVIEW"


def test_net_quantity_validation():
    """Test Net Quantity validation."""
    # Positive
    text = "Net Quantity: 400 g"
    res = FSSAIRuleVerifier._verify_net_quantity(text)
    assert res["status"] == "PRESENT"

    # Invalid: unit omitted
    text_nounit = "Net Quantity: 200"
    res_nounit = FSSAIRuleVerifier._verify_net_quantity(text_nounit)
    assert res_nounit["status"] == "INVALID"

    # A unit elsewhere in the nutrition table is not the net quantity.
    res_unrelated = FSSAIRuleVerifier._verify_net_quantity(
        "Nutrition per 100g: Energy 250 kcal, Protein 8g, Fat 2g."
    )
    assert res_unrelated["status"] == "MISSING"


def test_mrp_validation():
    """Test Retail Sale Price (MRP) validation."""
    # Positive
    text = "MRP: Rs. 50.00 (inclusive of all taxes)"
    res = FSSAIRuleVerifier._verify_mrp(text)
    assert res["status"] == "PRESENT"

    # Presence detection does not depend on the tax clause.
    text_notax = "MRP: Rs. 50.00"
    res_notax = FSSAIRuleVerifier._verify_mrp(text_notax)
    assert res_notax["status"] == "PRESENT"

    assert FSSAIRuleVerifier._verify_mrp(
        "MRP: ₹ 1,250.00"
    )["status"] == "PRESENT"

    # Punctuation is commonly printed between the letters in the M.R.P. abbreviation.
    assert FSSAIRuleVerifier._verify_mrp(
        "M.R.P. Rs. 50.00"
    )["status"] == "PRESENT"

    # OCR may preserve the printed tax qualifier and read the rupee sign as '#'.
    assert FSSAIRuleVerifier._verify_mrp(
        "MRP (incl. of all taxes):\n#40.00"
    )["status"] == "PRESENT"

    # OCR can separate the MRP label from its currency amount with address text.
    assert FSSAIRuleVerifier._verify_mrp(
        "MRP (incl. of all taxes):\nBengaluru - 560058, Karnataka, India.\n#40.00"
    )["status"] == "PRESENT"

    # Do not treat an address PIN code as an MRP when no currency marker is read.
    assert FSSAIRuleVerifier._verify_mrp(
        "MRP (incl. of all taxes):\nBengaluru - 560058, Karnataka, India."
    )["status"] == "MISSING"


def test_fssai_license_validation():
    """Test FSSAI 14-Digit Licence Number validation."""
    # Positive: authentic 14 digits
    text = "FSSAI Lic. No. 10019064001234"
    res = FSSAIRuleVerifier._verify_fssai_license(text)
    assert res["status"] == "PRESENT"

    # The printed logo word may occur between FSSAI and the licence label.
    res_logo = FSSAIRuleVerifier._verify_fssai_license(
        "FSSAI Logo Lic. No. 10019064001234"
    )
    assert res_logo["status"] == "PRESENT"

    # Invalid: only 8 digits
    text_8dig = "FSSAI License: 12345678"
    res_8dig = FSSAIRuleVerifier._verify_fssai_license(text_8dig)
    assert res_8dig["status"] == "INVALID"

    # An unrelated 14-digit identifier is not an FSSAI licence.
    res_unrelated = FSSAIRuleVerifier._verify_fssai_license(
        "Barcode reference 10019064001234"
    )
    assert res_unrelated["status"] == "MISSING"

    # Missing
    res_miss = FSSAIRuleVerifier._verify_fssai_license("Delicious food product.")
    assert res_miss["status"] == "MISSING"


def test_batch_number_validation():
    """Test Batch Number validation."""
    text = "Batch No: WBD402"
    res = FSSAIRuleVerifier._verify_batch_number(text)
    assert res["status"] == "PRESENT"

    text_nil = "Batch No: None"
    res_nil = FSSAIRuleVerifier._verify_batch_number(text_nil)
    assert res_nil["status"] == "INVALID"


def test_date_marking_validation():
    """Test Date Marking validation."""
    # Positive: both Mfg and Expiry
    text = "Date of Mfg: 12/10/2026. Best Before: 17/10/2026."
    res = FSSAIRuleVerifier._verify_date_marking(text)
    assert res["status"] == "PRESENT"

    # Unreadable/incomplete date pair is missing, not a separate invalid state.
    text_today = "Mfg Date: Today"
    res_today = FSSAIRuleVerifier._verify_date_marking(text_today)
    assert res_today["status"] == "MISSING"

    res_placeholder = FSSAIRuleVerifier._verify_date_marking(
        "Mfg: not printed. Best Before: not available."
    )
    assert res_placeholder["status"] == "MISSING"

    res_impossible = FSSAIRuleVerifier._verify_date_marking(
        "Mfg: 32/13/2026. Best Before: 17/10/2026."
    )
    assert res_impossible["status"] == "MISSING"

    ocr_split_labels = (
        "Date of Packaging: 01/10/2026. Best Be fore 6 months from packaging"
    )
    assert FSSAIRuleVerifier._verify_date_marking(ocr_split_labels)["status"] == "PRESENT"

    written_month_dates = (
        "Mfg. Date: 12 Oct 2026. Best Before: 12 Apr 2027."
    )
    assert FSSAIRuleVerifier._verify_date_marking(written_month_dates)["status"] == "PRESENT"


def test_instructions_and_origin():
    """Test Storage Instructions and Country of Origin."""
    text = "Store in a cool and dry place. Country of Origin: India."
    res_inst = FSSAIRuleVerifier._verify_instructions(text)
    res_orig = FSSAIRuleVerifier._verify_country_of_origin(text)
    assert res_inst["status"] == "PRESENT"
    assert res_orig["status"] == "PRESENT"


def test_verify_all_summary_scoring():
    """Test overall scoring and conservative compliance classification."""
    compliant_label = (
        "WHOLE WHEAT BREAD. "
        "Ingredients: Whole Wheat Flour (62%), Water, Yeast, Sugar, Salt, Edible Vegetable Oil, Preservative (INS 282). "
        "Nutritional info per 100g: Energy 245 kcal, Protein 8.5g, Carbohydrates 48g, Total Sugars 4.2g, Added Sugars 3.0g, Total Fat 2.1g, Saturated Fat 0.4g, Trans Fat 0g, Sodium 420mg. "
        "Vegetarian Logo (Green Circle in Square). "
        "Mfd by: Surya Bakers Pvt Ltd, Plot 45, Sector 18, Gurugram, Haryana - 122015. "
        "Customer Care: 1800-200-8899, care@suryabakers.com. "
        "Net Wt: 400 g. MRP Rs. 50.00 (inclusive of all taxes). "
        "FSSAI Lic. No. 10019064001234. Batch No: WBD402. "
        "Mfg: 12/10/2026. Best Before: 17/10/2026. "
        "Store in a cool and dry place. Product of India."
    )
    result = FSSAIRuleVerifier.verify_all(
        compliant_label,
        {"detected": True, "type": "VEGETARIAN"}
    )
    assert result["score"] == 100.0
    assert result["compliance_status"] == "COMPLIANT"
    assert len(result["fields"]) == 14
    assert set(field["status"] for field in result["fields"].values()) == {"PRESENT"}
    assert set(result["status_counts"]) == {"PRESENT", "MISSING"}


def test_summary_requires_all_fields_for_compliance():
    """A scan is compliant only when every required field is present."""
    fields = {
        key: {"status": "PRESENT"}
        for key in FIELD_DEFINITIONS
    }
    assert FSSAIRuleVerifier.summarize_fields(fields)["compliance_status"] == "COMPLIANT"

    fields["country_of_origin"] = {"status": "MISSING"}
    summary = FSSAIRuleVerifier.summarize_fields(fields)
    assert summary["score"] == 98.0
    assert summary["compliance_status"] == "NON_COMPLIANT"

    fields["fssai_license"] = {"status": "INVALID"}
    assert FSSAIRuleVerifier.summarize_fields(fields)["compliance_status"] == "NON_COMPLIANT"
    assert FSSAIRuleVerifier.summarize_fields(fields)["status_counts"] == {
        "PRESENT": 12,
        "MISSING": 2
    }


def test_verify_all_exposes_only_present_or_missing():
    """Unconfirmed and invalid findings are displayed as missing."""
    result = FSSAIRuleVerifier.verify_all(
        "WHOLE WHEAT BREAD. MRP Rs. 45.00. "
        "Nutrition Information: Energy 250 kcal, Protein 8g. "
        "Mfg: Today. Best Before: none."
    )
    statuses = {field["status"] for field in result["fields"].values()}
    assert statuses <= {"PRESENT", "MISSING"}
    assert result["fields"]["nutrition"]["status"] == "PRESENT"
    assert result["fields"]["mrp"]["status"] == "PRESENT"
    assert result["fields"]["date_marking"]["status"] == "MISSING"
    assert result["fields"]["veg_nonveg"]["status"] == "MISSING"
    assert result["compliance_status"] == "NON_COMPLIANT"
    assert result["status_counts"] == {"PRESENT": 3, "MISSING": 11}
