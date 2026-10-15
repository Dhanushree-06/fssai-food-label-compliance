"""
Standalone Test Runner using Python Standard Library unittest
AI-Based Food Label Compliance Verification Platform
"""

import sys
import os
import unittest
import traceback

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


class FSSAIRulesTestCase(unittest.TestCase):
    """Test suite for 14 FSSAI field validators."""

    def test_field_definitions_count(self):
        from tests.test_fssai_rules import test_field_definitions_count
        test_field_definitions_count()

    def test_food_name_validation(self):
        from tests.test_fssai_rules import test_food_name_validation
        test_food_name_validation()

    def test_ingredients_validation(self):
        from tests.test_fssai_rules import test_ingredients_validation
        test_ingredients_validation()

    def test_nutrition_validation(self):
        from tests.test_fssai_rules import test_nutrition_validation
        test_nutrition_validation()

    def test_veg_nonveg_validation(self):
        from tests.test_fssai_rules import test_veg_nonveg_validation
        test_veg_nonveg_validation()

    def test_additives_validation(self):
        from tests.test_fssai_rules import test_additives_validation
        test_additives_validation()

    def test_manufacturer_validation(self):
        from tests.test_fssai_rules import test_manufacturer_validation
        test_manufacturer_validation()

    def test_customer_care_validation(self):
        from tests.test_fssai_rules import test_customer_care_validation
        test_customer_care_validation()

    def test_net_quantity_validation(self):
        from tests.test_fssai_rules import test_net_quantity_validation
        test_net_quantity_validation()

    def test_mrp_validation(self):
        from tests.test_fssai_rules import test_mrp_validation
        test_mrp_validation()

    def test_fssai_license_validation(self):
        from tests.test_fssai_rules import test_fssai_license_validation
        test_fssai_license_validation()

    def test_batch_number_validation(self):
        from tests.test_fssai_rules import test_batch_number_validation
        test_batch_number_validation()

    def test_date_marking_validation(self):
        from tests.test_fssai_rules import test_date_marking_validation
        test_date_marking_validation()

    def test_instructions_and_origin(self):
        from tests.test_fssai_rules import test_instructions_and_origin
        test_instructions_and_origin()

    def test_verify_all_summary_scoring(self):
        from tests.test_fssai_rules import test_verify_all_summary_scoring
        test_verify_all_summary_scoring()

    def test_summary_requires_all_fields_for_compliance(self):
        from tests.test_fssai_rules import test_summary_requires_all_fields_for_compliance
        test_summary_requires_all_fields_for_compliance()


class MLModelTestCase(unittest.TestCase):
    """Test suite for ML model and 150-row dataset."""

    def test_dataset_exact_150_rows(self):
        from tests.test_ml_model import test_dataset_exact_150_rows
        test_dataset_exact_150_rows()

    def test_model_artifacts_exist(self):
        from tests.test_ml_model import test_model_artifacts_exist
        test_model_artifacts_exist()

    def test_model_metrics_integrity(self):
        from tests.test_ml_model import test_model_metrics_integrity
        test_model_metrics_integrity()

    def test_model_prediction_inference(self):
        from tests.test_ml_model import test_model_prediction_inference
        test_model_prediction_inference()


class ImageProcessingTestCase(unittest.TestCase):
    """Test suite for OpenCV image preprocessing."""

    def test_deskew_image_synthetic(self):
        from tests.test_image_processing import test_deskew_image_synthetic
        test_deskew_image_synthetic()

    def test_enhance_contrast(self):
        from tests.test_image_processing import test_enhance_contrast
        test_enhance_contrast()

    def test_preprocess_pipeline_on_sample(self):
        from tests.test_image_processing import test_preprocess_pipeline_on_sample
        test_preprocess_pipeline_on_sample()

    def test_detect_veg_symbol(self):
        from tests.test_image_processing import test_detect_veg_symbol
        test_detect_veg_symbol()

    def test_ocr_reads_image_content_instead_of_filename(self):
        from tests.test_image_processing import test_ocr_reads_image_content_instead_of_filename
        test_ocr_reads_image_content_instead_of_filename()

    def test_unavailable_opencv_fallback_does_not_invent_label_text(self):
        from tests.test_image_processing import test_unavailable_opencv_fallback_does_not_invent_label_text
        test_unavailable_opencv_fallback_does_not_invent_label_text()


class FlaskRoutesTestCase(unittest.TestCase):
    """Test suite for Flask routes and workflows."""

    def setUp(self):
        from app import create_app
        from app.models import db
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        from app.models import db
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_home_page(self):
        from tests.test_routes import test_home_page
        test_home_page(self.client)

    def test_about_page(self):
        from tests.test_routes import test_about_page
        test_about_page(self.client)

    def test_verify_get_page(self):
        from tests.test_routes import test_verify_get_page
        test_verify_get_page(self.client)

    def test_verify_post_sample(self):
        from tests.test_routes import test_verify_post_sample
        test_verify_post_sample(self.client)

    def test_recheck_api_workflow(self):
        from tests.test_routes import test_recheck_api_workflow
        test_recheck_api_workflow(self.client)

    def test_history_and_export(self):
        from tests.test_routes import test_history_and_export
        test_history_and_export(self.client)

    def test_api_verify_text(self):
        from tests.test_routes import test_api_verify_text
        test_api_verify_text(self.client)

    def test_download_zip_route(self):
        from tests.test_routes import test_download_zip_route
        test_download_zip_route(self.client)


def main():
    print("======================================================================")
    print(" Running FSSAI Verification Platform Unit & Integration Tests")
    print("======================================================================")
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    suite.addTests(loader.loadTestsFromTestCase(FSSAIRulesTestCase))
    suite.addTests(loader.loadTestsFromTestCase(MLModelTestCase))
    suite.addTests(loader.loadTestsFromTestCase(ImageProcessingTestCase))
    suite.addTests(loader.loadTestsFromTestCase(FlaskRoutesTestCase))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n======================================================================")
    print(f" Tests Run: {result.testsRun}")
    print(f" Errors:    {len(result.errors)}")
    print(f" Failures:  {len(result.failures)}")
    print(f" Success:   {result.wasSuccessful()}")
    print("======================================================================\n")

    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
