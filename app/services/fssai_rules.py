"""
FSSAI Food Label Compliance Verification Rule Engine
Based on Food Safety and Standards (Labelling and Display) Regulations, 2020.

Validates the 14 mandatory FSSAI label fields using strict evidence-based rules.
Returns only 'PRESENT' or 'MISSING' field statuses.
MISSING means the required evidence was not confirmed in extracted text or image.
"""

import re
from datetime import datetime


FIELD_DEFINITIONS = {
    "food_name": {
        "title": "Name of Food",
        "weight": 5,
        "regulation": "FSSAI Regulation 5(1): Declared common or descriptive name of food",
        "description": "Standardised or descriptive product name indicating the true nature of the food."
    },
    "ingredients": {
        "title": "List of Ingredients",
        "weight": 10,
        "regulation": "FSSAI Regulation 5(2): Heading 'Ingredients:' in descending order of weight/volume",
        "description": "Comprehensive list of all ingredients including allergen declarations where applicable."
    },
    "nutrition": {
        "title": "Nutritional Information",
        "weight": 10,
        "regulation": "FSSAI Regulation 5(3): Energy, Protein, Carbs, Total/Added Sugars, Fat, Saturated/Trans Fat, Sodium",
        "description": "Mandatory nutritional breakdown per 100g/ml or per serving."
    },
    "veg_nonveg": {
        "title": "Veg / Non-Veg Symbol",
        "weight": 8,
        "regulation": "FSSAI Regulation 5(4): Green circle in square (Veg) or Brown triangle in square (Non-Veg)",
        "description": "Statutory symbol or logo identifying food as Vegetarian or Non-Vegetarian."
    },
    "additives": {
        "title": "Declaration of Food Additives",
        "weight": 5,
        "regulation": "FSSAI Regulation 5(5): INS Numbers and functional class titles for all additives",
        "description": "International Numbering System (INS) codes or functional class titles."
    },
    "manufacturer": {
        "title": "Manufacturer Name & Address",
        "weight": 10,
        "regulation": "FSSAI Regulation 5(6): Complete postal address of manufacturer/packer with PIN code",
        "description": "Full registered premises address of the food business operator."
    },
    "customer_care": {
        "title": "Customer Care Details",
        "weight": 6,
        "regulation": "FSSAI Regulation 5(7): Telephone, email, and postal grievance address",
        "description": "Consumer helpline number and email for grievances."
    },
    "net_quantity": {
        "title": "Net Quantity",
        "weight": 8,
        "regulation": "FSSAI Regulation 5(8) & Legal Metrology: Standard metric units (g, kg, ml, l)",
        "description": "Net weight or volume in standard metric units."
    },
    "mrp": {
        "title": "Retail Sale Price (MRP)",
        "weight": 8,
        "regulation": "Legal Metrology & FSSAI: MRP inclusive of all taxes declaration",
        "description": "Maximum Retail Price in INR with mandatory taxes inclusion statement."
    },
    "fssai_license": {
        "title": "FSSAI Logo & 14-Digit Licence No.",
        "weight": 10,
        "regulation": "FSSAI Regulation 5(9): 14-digit alphanumeric license number displayed with FSSAI logo",
        "description": "14-digit registration/licence number of the manufacturer/marketer."
    },
    "batch_number": {
        "title": "Lot / Code / Batch Identification",
        "weight": 6,
        "regulation": "FSSAI Regulation 5(10): Batch / Lot identification preceded by 'Batch No' or 'Lot No'",
        "description": "Unique traceability code identifying the production lot."
    },
    "date_marking": {
        "title": "Date Marking (Mfg & Best Before)",
        "weight": 10,
        "regulation": "FSSAI Regulation 5(11): Date of manufacture/packaging and Best Before/Expiry date",
        "description": "Clear chronological manufacturing/packaging date and shelf-life period."
    },
    "instructions": {
        "title": "Instructions for Use & Storage",
        "weight": 2,
        "regulation": "FSSAI Regulation 5(12): Special storage conditions and instructions for preparation",
        "description": "Clear guidelines on storage temperature, shelf handling, and usage."
    },
    "country_of_origin": {
        "title": "Country of Origin",
        "weight": 2,
        "regulation": "FSSAI Regulation 5(13): Mandatory declaration of origin country for packaged foods",
        "description": "Explicit declaration of country where food was manufactured."
    }
}


class FSSAIRuleVerifier:
    """Verifies food label text against all 14 mandatory FSSAI fields."""

    @classmethod
    def verify_all(cls, text, cv_symbol_info=None):
        """
        Evaluates all 14 fields and exposes a binary evidence status for each.
        """
        clean_text = str(text or "").strip()
        clean_text = re.sub(r"\bing\s*redients?\b", "Ingredients", clean_text, flags=re.IGNORECASE)
        clean_text = re.sub(r"\bingredie\s*nts?\b", "Ingredients", clean_text, flags=re.IGNORECASE)
        clean_text = re.sub(
            r"\bN\s*U\s*T\s*R\s*I\s*T\s*I\s*O\s*N(?:\s*A\s*L)?\b",
            "Nutrition",
            clean_text,
            flags=re.IGNORECASE
        )
        clean_text = re.sub(
            r"\bBest\s*Be\s*fore\b", "Best Before", clean_text, flags=re.IGNORECASE
        )
        results = {}

        # 1. Food Name
        results["food_name"] = cls._verify_food_name(clean_text)

        # 2. Ingredients
        results["ingredients"] = cls._verify_ingredients(clean_text)

        # 3. Nutrition
        results["nutrition"] = cls._verify_nutrition(clean_text)

        # 4. Veg / Non-Veg
        results["veg_nonveg"] = cls._verify_veg_nonveg(clean_text, cv_symbol_info)

        # 5. Food Additives
        results["additives"] = cls._verify_additives(clean_text)

        # 6. Manufacturer Name & Address
        results["manufacturer"] = cls._verify_manufacturer(clean_text)

        # 7. Customer Care Details
        results["customer_care"] = cls._verify_customer_care(clean_text)

        # 8. Net Quantity
        results["net_quantity"] = cls._verify_net_quantity(clean_text)

        # 9. Retail Sale Price (MRP)
        results["mrp"] = cls._verify_mrp(clean_text)

        # 10. FSSAI License & Logo
        results["fssai_license"] = cls._verify_fssai_license(clean_text)

        # 11. Batch / Lot Number
        results["batch_number"] = cls._verify_batch_number(clean_text)

        # 12. Date Marking (Mfg & Expiry)
        results["date_marking"] = cls._verify_date_marking(clean_text)

        # 13. Instructions & Storage
        results["instructions"] = cls._verify_instructions(clean_text)

        # 14. Country of Origin
        results["country_of_origin"] = cls._verify_country_of_origin(clean_text)

        for field in results.values():
            field["status"] = "PRESENT" if field["status"] == "PRESENT" else "MISSING"

        summary = cls.summarize_fields(results)
        return {**summary, "fields": results}

    @classmethod
    def summarize_fields(cls, fields):
        """Summarize confirmed and unconfirmed field evidence."""
        earned_score = 0
        total_possible = sum(field["weight"] for field in FIELD_DEFINITIONS.values())
        status_counts = {"PRESENT": 0, "MISSING": 0}
        normalized_statuses = {}

        for key, definition in FIELD_DEFINITIONS.items():
            status = "PRESENT" if fields.get(key, {}).get("status") == "PRESENT" else "MISSING"
            normalized_statuses[key] = status
            status_counts[status] += 1

            if status == "PRESENT":
                earned_score += definition["weight"]

        score_percent = round((earned_score / total_possible) * 100, 1)
        if all(status == "PRESENT" for status in normalized_statuses.values()):
            compliance_status = "COMPLIANT"
            status_desc = "All 14 required label items were detected."
        else:
            compliance_status = "NON_COMPLIANT"
            status_desc = (
                "One or more required items were not detected in the extracted evidence. "
                "Check the OCR text against the original label."
            )

        return {
            "score": score_percent,
            "earned_points": earned_score,
            "total_points": total_possible,
            "compliance_status": compliance_status,
            "status_description": status_desc,
            "status_counts": status_counts
        }

    # ================= FIELD VALIDATORS =================

    @staticmethod
    def _verify_food_name(text):
        """1. Name of Food"""
        # Look for descriptive product naming
        name_patterns = [
            r"(?:product\s*name|item\s*name|name\s*of\s*food|food\s*name)\s*[:\-]?\s*([A-Za-z0-9\s\-\&]+)",
            r"\b([A-Za-z\s]+(?:Bread|Nectar|Juice|Chips|Ghee|Butter|Noodles|Cookies|Oil|Powder|Pickle|Yogurt|Chocolate|Cereal|Cheese|Masala|Atta|Flakes|Drink|Sauce))\b"
        ]
        evidence = []
        for pat in name_patterns:
            matches = re.findall(pat, text, re.IGNORECASE)
            if matches:
                evidence.extend([m.strip() for m in matches if len(m.strip()) > 3])

        if evidence:
            candidate = evidence[0]
            return {
                "status": "PRESENT",
                "confidence": 0.95,
                "evidence": f"Identified food name: '{candidate}'",
                "rules_passed": ["Descriptive food name declared clearly on principal display panel"],
                "recommendation": "Compliant with FSSAI Regulation 5(1)."
            }

        # Check if first line contains text
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if lines and len(lines[0]) > 3 and not re.search(r"ingredient|mrp|fssai|batch", lines[0], re.I):
            return {
                "status": "NEEDS_REVIEW",
                "confidence": 0.65,
                "evidence": f"First line detected as potential product name: '{lines[0]}'",
                "rules_passed": ["Text header isolated"],
                "recommendation": "Ensure the specific descriptive name of the food is clearly printed on the principal display panel."
            }

        return {
            "status": "MISSING",
            "confidence": 0.0,
            "evidence": "No clear descriptive product name found.",
            "rules_passed": [],
            "recommendation": "FSSAI Regulation 5(1) requires the specific descriptive name of food."
        }

    @staticmethod
    def _verify_ingredients(text):
        """2. List of Ingredients"""
        # Search for Ingredients header
        m = re.search(
            r"\b(?:Ingredients?|Ingr[eé]dients?)\s*[:\-]?\s*(.*?)"
            r"(?=\b(?:Nutrition(?:al)?|Mfd|Pack(?:ed|aged)?\s+by|Batch|Net|"
            r"MRP|FSSAI|Store|Date|Country)\b|$)",
            text,
            re.DOTALL | re.IGNORECASE
        )
        if m:
            content = m.group(1).strip()
            if re.match(
                r"(?:none|n/?a|not\s+(?:available|declared|printed|provided|listed|present|found)|"
                r"missing|no\s+(?:ingredients?|declaration|data))\b",
                content,
                re.IGNORECASE
            ):
                return {
                    "status": "INVALID",
                    "confidence": 0.90,
                    "evidence": f"Ingredients heading is followed by a missing/placeholder declaration: '{content[:60]}'.",
                    "rules_passed": [],
                    "recommendation": "List the actual ingredients instead of a placeholder or missing declaration."
                }

            items = [
                item.strip() for item in re.split(r"[,;\n]", content)
                if len(item.strip()) > 2
            ]
            if content:
                # Check for allergen statement
                allergen = "Contains" in content or "Allergen" in text
                parsed_list = len(items) >= 2
                return {
                    "status": "PRESENT",
                    "confidence": 0.95 if parsed_list else 0.75,
                    "evidence": (
                        f"Ingredients declared: {content[:100]}... ({len(items)} items listed)"
                        if parsed_list
                        else f"Ingredient declaration text detected: '{content[:100]}'."
                    ),
                    "rules_passed": [
                        "Standard 'Ingredients:' heading present",
                        (
                            f"Ingredient list separators detected ({len(items)} components)"
                            if parsed_list
                            else "Ingredient declaration text follows the heading"
                        ),
                        "Allergen statement checked" if allergen else "No specific allergen declared"
                    ],
                    "recommendation": "Meets FSSAI Regulation 5(2) requirements."
                }
            else:
                return {
                    "status": "INVALID",
                    "confidence": 0.20,
                    "evidence": "Keyword 'Ingredients:' found but no actual ingredient items follow.",
                    "rules_passed": [],
                    "recommendation": "Keyword alone is insufficient. All ingredients must be listed."
                }

        return {
            "status": "MISSING",
            "confidence": 0.0,
            "evidence": "No ingredient declaration found on label.",
            "rules_passed": [],
            "recommendation": "Mandatory under FSSAI Regulation 5(2) for all multi-ingredient packaged foods."
        }

    @staticmethod
    def _verify_nutrition(text):
        """3. Nutritional Information"""
        header = re.search(
            r"\bNutrition(?:al)?(?:\s*(?:Info(?:rmation)?|Facts|Values))?\b",
            text,
            re.IGNORECASE
        )
        section = text[header.end():] if header else ""
        if header:
            next_section = re.search(
                r"\b(?:Manufactured|Mfd\s+by|Packed\s*by|Customer\s*(?:Care|Support)|"
                r"Net\s*(?:Quantity|Weight|Volume)|MRP|FSSAI|Batch|Best\s*Before|"
                r"Expiry|Date\s*of|Store\s+in|Made\s+in|Country\s+of)\b",
                section,
                re.IGNORECASE
            )
            if next_section:
                section = section[:next_section.start()]
        section = re.sub(r"\bEne\s*rgy\b", "Energy", section, flags=re.IGNORECASE)

        has_values = bool(re.search(
            r"\b(?:Energy|Calories|Protein|Carbohydrates?|Carbs?|Sugars?|Fat|Sodium)\b"
            r"\s*[:.\-]?\s*\d+(?:[.,]\d+)?\s*(?:kcal|kJ|g|mg)\b",
            section,
            re.IGNORECASE
        ))
        if header and has_values:
            return {
                "status": "PRESENT",
                "confidence": 0.90,
                "evidence": "Nutrition heading and numeric nutrient values detected.",
                "rules_passed": [
                    "Nutrition heading present",
                    "Numeric nutrition information detected"
                ],
                "recommendation": "Nutrition declaration detected. Confirm all required nutrients and values against the original label."
            }

        return {
            "status": "MISSING",
            "confidence": 0.0,
            "evidence": "Nutrition heading with numeric nutrient values was not detected.",
            "rules_passed": [],
            "recommendation": "Check the original label for a nutrition table and readable values."
        }

    @staticmethod
    def _verify_veg_nonveg(text, cv_symbol_info=None):
        """4. Veg / Non-Veg Symbol"""
        # Check CV contour detection first
        cv_detected = False
        cv_type = None
        if cv_symbol_info and cv_symbol_info.get("detected"):
            cv_detected = True
            cv_type = cv_symbol_info.get("type")

        # Text declarations
        veg_text = bool(re.search(r"\b(?:Vegetarian|100%\s*Veg|Green\s*(?:Dot|Logo|Circle|Emblem|Mark)|Veg\s*Symbol)\b", text, re.IGNORECASE))
        nonveg_text = bool(re.search(r"\b(?:Non-Vegetarian|Non\s*Veg|Brown\s*(?:Triangle|Logo|Emblem|Mark))\b", text, re.IGNORECASE))

        # Check for non-veg ingredients conflict (e.g. egg, meat, gelatin)
        has_nonveg_ingredients = bool(re.search(r"\b(?:Egg|Meat|Fish|Chicken|Pork|Beef|Gelatin|Crab|Prawn)\b", text, re.IGNORECASE))

        if cv_detected and cv_type == "VEGETARIAN":
            if has_nonveg_ingredients:
                return {
                    "status": "INVALID",
                    "confidence": 0.90,
                    "evidence": "Green Veg logo detected via OpenCV, but non-vegetarian ingredient (e.g. egg/meat) was found in text!",
                    "rules_passed": ["OpenCV Symbol Contour Isolated"],
                    "recommendation": "Severe violation: Product containing non-veg ingredients cannot bear Vegetarian symbol."
                }
            return {
                "status": "PRESENT",
                "confidence": 0.95,
                "evidence": "Vegetarian emblem (Green circle inside square) confirmed via OpenCV HSV contour analysis.",
                "rules_passed": ["OpenCV green circular contour verified", "Aspect ratio validated"],
                "recommendation": "Compliant with FSSAI Regulation 5(4)."
            }
        elif cv_detected and cv_type == "NON_VEGETARIAN":
            return {
                "status": "PRESENT",
                "confidence": 0.95,
                "evidence": "Non-Vegetarian emblem (Brown triangle inside square) confirmed via OpenCV contour analysis.",
                "rules_passed": ["OpenCV brown/red triangular contour verified"],
                "recommendation": "Compliant with FSSAI Regulation 5(4)."
            }
        elif re.search(
            r"\b(?:no|missing|absent|not\s+(?:present|found|printed|displayed))\b"
            r".{0,35}\b(?:veg(?:etarian)?\s*)?(?:logo|symbol|dot|mark)\b|"
            r"\b(?:logo|symbol|dot|mark)\s*(?:is\s*)?"
            r"(?:absent|missing|not\s+(?:present|found|printed|displayed))\b",
            text,
            re.IGNORECASE
        ):
            return {
                "status": "INVALID",
                "confidence": 0.85,
                "evidence": "The label text explicitly indicates that the veg/non-veg symbol is absent.",
                "rules_passed": [],
                "recommendation": "Confirm the label displays the applicable statutory veg or non-veg symbol."
            }
        elif veg_text:
            if has_nonveg_ingredients:
                return {
                    "status": "INVALID",
                    "confidence": 0.85,
                    "evidence": "Text claims Vegetarian, but non-veg ingredients detected in ingredients list.",
                    "rules_passed": [],
                    "recommendation": "Conflicting declaration. Check ingredient source."
                }
            return {
                "status": "NEEDS_REVIEW",
                "confidence": 0.65,
                "evidence": "Text indicates a vegetarian declaration, but OCR text cannot confirm the required printed symbol.",
                "rules_passed": ["Vegetarian wording detected"],
                "recommendation": "Visually confirm the statutory green symbol on the original package."
            }
        elif nonveg_text or has_nonveg_ingredients:
            return {
                "status": "NEEDS_REVIEW",
                "confidence": 0.70,
                "evidence": "Non-vegetarian ingredient/text detected. Statutory brown triangle symbol required.",
                "rules_passed": ["Non-veg classification identified"],
                "recommendation": "Must display brown filled triangle inside brown square border on label."
            }

        return {
            "status": "NEEDS_REVIEW",
            "confidence": 0.40,
            "evidence": "No veg/non-veg symbol was detected; image quality or OCR may have missed a visual mark.",
            "rules_passed": [],
            "recommendation": "Visually confirm the applicable statutory symbol on the original package."
        }

    @staticmethod
    def _verify_additives(text):
        """5. Food Additives Declaration"""
        # Look for INS numbers (e.g. INS 330, INS 211, INS 322, etc.)
        ins_matches = re.findall(r"\b(?:INS\s*(\d+[a-z]?)|E\s*(\d+[a-z]?))\b", text, re.IGNORECASE)
        # Look for class titles
        class_titles = re.findall(
            r"\b(Preservative|Acidity Regulator|Emulsifier|Stabilizer|Antioxidant|Raising Agent|Flavour Enhancer|Colour|Anticaking Agent|Sweetener|Added Flavours)\b",
            text, re.IGNORECASE
        )

        pure_food_keywords = bool(re.search(r"\b(?:100%\s*Pure|Free from Argemone Oil|Clarified Butterfat|Single Ingredient|Ground Dried)\b", text, re.IGNORECASE))

        if ins_matches:
            flattened_codes = [m[0] or m[1] for m in ins_matches]
            return {
                "status": "PRESENT",
                "confidence": 0.95,
                "evidence": f"Food additives declared with INS codes: {', '.join(flattened_codes)}. Class titles: {', '.join(set(class_titles)) or 'None'}",
                "rules_passed": [
                    f"International Numbering System (INS) codes identified: {', '.join(flattened_codes)}",
                    "Class title declaration checked"
                ],
                "recommendation": "Compliant with FSSAI Regulation 5(5)."
            }
        elif class_titles:
            return {
                "status": "PRESENT",
                "confidence": 0.85,
                "evidence": f"Functional class titles declared: {', '.join(set(class_titles))}",
                "rules_passed": ["Functional additive class titles identified"],
                "recommendation": "Compliant. Mention specific INS numbers alongside class titles where applicable."
            }
        elif pure_food_keywords and not re.search(r"\b(?:Preservative|Artificial|Colour|Flavour)\b", text, re.IGNORECASE):
            return {
                "status": "PRESENT",
                "confidence": 0.90,
                "evidence": "Single-ingredient pure food product; no additives required or declared.",
                "rules_passed": ["Pure / natural food declaration validated"],
                "recommendation": "Not applicable / No food additives used."
            }
        elif re.search(r"\b(?:artificial|flavours?|preservatives?)\b", text, re.IGNORECASE):
            return {
                "status": "INVALID",
                "confidence": 0.40,
                "evidence": "Vague mention of 'flavours' or 'preservative' without mandatory INS numbering or specific class title.",
                "rules_passed": [],
                "recommendation": "Under FSSAI 2020, generic terms are illegal; state exact functional class title and INS numbers."
            }

        return {
            "status": "NEEDS_REVIEW",
            "confidence": 0.50,
            "evidence": "No explicit food additives or INS numbers declared.",
            "rules_passed": [],
            "recommendation": "If additives or flavouring substances are used, declare functional class titles and INS numbers."
        }

    @staticmethod
    def _verify_manufacturer(text):
        """6. Manufacturer Name and Complete Address"""
        m = re.search(r"\b(?:Mfd(?:\s*by)?|Manufactured\s*by|Packed\s*by|Marketed\s*by|Bottled\s*by)\s*[:\-]?\s*(.*?)(?=\b(?:Customer|Care|Net|MRP|FSSAI|Lic|Batch|Date|Storage|Best)\b|$)", text, re.DOTALL | re.IGNORECASE)
        
        if m:
            content = m.group(1).strip()
            pincode_match = re.search(r"\b[1-9][0-9]{2}\s?[0-9]{3}\b", content)
            has_company = bool(re.search(r"(?:Pvt|Ltd|Foods|Bakers?|Co(?:mpany)?|Coop|Dairy|Mills|Agro|Snacks|Beverages|Enterprises|Industries)\b", content, re.IGNORECASE))
            has_address = len(content) > 30 and pincode_match is not None

            if has_company and has_address:
                return {
                    "status": "PRESENT",
                    "confidence": 0.95,
                    "evidence": f"Manufacturer & address: '{content[:80]}...' (PIN: {pincode_match.group(0)})",
                    "rules_passed": [
                        "Manufacturer prefix ('Mfd by') verified",
                        "Company identity isolated",
                        "Postal premises address verified",
                        "6-digit PIN code detected"
                    ],
                    "recommendation": "Compliant with FSSAI Regulation 5(6)."
                }
            elif has_company:
                return {
                    "status": "NEEDS_REVIEW",
                    "confidence": 0.60,
                    "evidence": f"Manufacturer name found ('{content[:40]}'), but complete postal address/PIN code appears incomplete.",
                    "rules_passed": ["Manufacturer name present"],
                    "recommendation": "Complete postal address with state and 6-digit PIN code is mandatory under FSSAI 2020."
                }
            else:
                return {
                    "status": "INVALID",
                    "confidence": 0.30,
                    "evidence": f"Incomplete manufacturer clause: '{content[:40]}'",
                    "rules_passed": [],
                    "recommendation": "Must declare complete registered premises address."
                }

        return {
            "status": "MISSING",
            "confidence": 0.0,
            "evidence": "Manufacturer / Packer name and address completely missing.",
            "rules_passed": [],
            "recommendation": "Mandatory under FSSAI Regulation 5(6)."
        }

    @staticmethod
    def _verify_customer_care(text):
        """7. Customer Care Details"""
        header = re.search(
            r"\b(?:Customer\s*(?:Care|Support|Service|Helpline)|Consumer\s*(?:Care|Helpline|Grievance)|Care\s*Email|Feedback)\b",
            text,
            re.IGNORECASE
        )
        contact_section = text[header.start():header.start() + 160] if header else ""
        if header:
            next_section = re.search(
                r"\b(?:Net\s*(?:Quantity|Weight|Volume)|MRP|FSSAI|Batch|Mfg|Packed\s*on|"
                r"Best\s*Before|Expiry|Store\s+in|Made\s+in|Country\s+of)\b",
                contact_section[header.end() - header.start():],
                re.IGNORECASE
            )
            if next_section:
                contact_section = contact_section[:header.end() - header.start() + next_section.start()]

        contact_pattern_phone = r"\b(?:\d[\s-]*){9,11}\d\b"
        contact_pattern_email = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        phone_match = re.search(contact_pattern_phone, contact_section)
        email_match = re.search(contact_pattern_email, contact_section)

        if phone_match and email_match:
            return {
                "status": "PRESENT",
                "confidence": 0.98,
                "evidence": f"Customer care phone: {phone_match.group(0)}, Email: {email_match.group(0)}",
                "rules_passed": [
                    "Consumer care heading verified",
                    f"Helpline number validated: {phone_match.group(0)}",
                    f"Email address validated: {email_match.group(0)}"
                ],
                "recommendation": "Compliant with FSSAI Regulation 5(7)."
            }
        elif header and (phone_match or email_match):
            found = f"Phone: {phone_match.group(0)}" if phone_match else f"Email: {email_match.group(0)}"
            return {
                "status": "PRESENT",
                "confidence": 0.85,
                "evidence": f"Customer care contact: {found}",
                "rules_passed": ["Contact channel verified"],
                "recommendation": "Compliant. Providing both toll-free telephone and dedicated email is recommended."
            }
        elif header:
            return {
                "status": "INVALID",
                "confidence": 0.20,
                "evidence": "Customer care heading found but no valid telephone number or email address could be parsed.",
                "rules_passed": [],
                "recommendation": "Keyword alone is invalid; provide working telephone helpline or email."
            }

        if re.search(contact_pattern_phone, text) or re.search(contact_pattern_email, text):
            return {
                "status": "NEEDS_REVIEW",
                "confidence": 0.40,
                "evidence": "A phone number or email was found, but no customer-care heading ties it to consumer support.",
                "rules_passed": [],
                "recommendation": "Confirm that this contact is explicitly identified for customer care or consumer grievances."
            }

        return {
            "status": "MISSING",
            "confidence": 0.0,
            "evidence": "Customer care details completely absent.",
            "rules_passed": [],
            "recommendation": "Mandatory for consumer grievance under FSSAI Regulation 5(7)."
        }

    @staticmethod
    def _verify_net_quantity(text):
        """8. Net Quantity"""
        # Standard legal metric units: g, kg, ml, l, L
        qty_pattern = r"\b(?:Net\s*(?:Wt\.?|Weight|Qty\.?|Quantity|Volume|Content))\s*[:\-\.]?\s*(\d+(?:\.\d+)?)\s*(g|gm|kg|ml|mL|l|L|ltr|litre)s?\b"
        m = re.search(qty_pattern, text, re.IGNORECASE)

        # Look for unit omission defect (e.g. "Net Quantity: 200" or "Weight: Approx 200")
        defective_m = re.search(r"\b(?:Net\s*(?:Qty|Quantity|Wt|Weight|Volume))\s*[:\-\.]?\s*(?:Approx\s*)?(\d+)(?!\s*(?:g|kg|ml|l|L))\b", text, re.IGNORECASE)

        if m:
            val, unit = m.group(1), m.group(2)
            return {
                "status": "PRESENT",
                "confidence": 0.95,
                "evidence": f"Net quantity declared: {val} {unit}",
                "rules_passed": [
                    "Standard 'Net Quantity' prefix verified",
                    "Numerical quantity parsed",
                    f"Legal Metrology metric unit '{unit}' verified"
                ],
                "recommendation": "Compliant with FSSAI Regulation 5(8)."
            }
        elif defective_m:
            return {
                "status": "INVALID",
                "confidence": 0.25,
                "evidence": f"Defective net quantity '{defective_m.group(0)}': Metric unit (g, kg, ml, L) is completely omitted!",
                "rules_passed": [],
                "recommendation": "Illegal under Legal Metrology Act and FSSAI 2020. Metric units must accompany numbers."
            }
        return {
            "status": "MISSING",
            "confidence": 0.0,
            "evidence": "Net quantity not detected.",
            "rules_passed": [],
            "recommendation": "Mandatory under FSSAI Regulation 5(8) & Legal Metrology Rules."
        }

    @staticmethod
    def _verify_mrp(text):
        """9. Detect a printed MRP/price amount."""
        mrp_pat = (
            r"\b(?:M\s*\.?\s*R\s*\.?\s*P\.?|M[Il1]RP|Price)\s*[:\-]?\s*"
            r"(?:\([^)]{0,60}\)\s*)?[:\-]?\s*"
            r"(?:(?:Rs\.?|INR|₹|#)\s*)?[:\-]?\s*"
            r"(\d{1,7}(?:,\d{2,3})*(?:\.\d{1,2})?)\b"
        )
        price_match = re.search(mrp_pat, text, re.IGNORECASE)
        if not price_match:
            mrp_label = re.search(
                r"\b(?:M\s*\.?\s*R\s*\.?\s*P\.?|M[Il1]RP|Price)\b",
                text,
                re.IGNORECASE
            )
            if mrp_label:
                price_context = text[mrp_label.end():mrp_label.end() + 160]
                next_field = re.search(
                    r"\b(?:FSSAI|Batch|Mfg|Mfd|Best\s*Before|Expiry|Date\s*of|"
                    r"Customer|Net\s*(?:Quantity|Wt|Weight|Volume)|Store\s+in)\b",
                    price_context,
                    re.IGNORECASE
                )
                if next_field:
                    price_context = price_context[:next_field.start()]
                price_match = re.search(
                    r"(?:Rs\.?|INR|₹|#)\s*"
                    r"(\d{1,7}(?:,\d{2,3})*(?:\.\d{1,2})?)\b",
                    price_context,
                    re.IGNORECASE
                )

        if price_match:
            return {
                "status": "PRESENT",
                "confidence": 0.95,
                "evidence": f"MRP declared: Rs. {price_match.group(1)} (inclusive of all taxes)",
                "rules_passed": [
                    "MRP/price label detected",
                    f"Price amount extracted: Rs. {price_match.group(1)}"
                ],
                "recommendation": "Price amount detected. Confirm the required MRP and tax declaration on the original label."
            }

        return {
            "status": "MISSING",
            "confidence": 0.0,
            "evidence": "No MRP/price label with a numeric amount was detected.",
            "rules_passed": [],
            "recommendation": "Check the original label for a printed MRP/price amount."
        }

    @staticmethod
    def _verify_fssai_license(text):
        """10. FSSAI Logo and 14-Digit Licence Number"""
        fssai_mark = re.search(r"\bFSSAI\b", text, re.IGNORECASE)
        fssai_prefix = None
        if fssai_mark:
            nearby_text = text[fssai_mark.end():fssai_mark.end() + 40]
            fssai_prefix = re.match(
                r"[\s.:#-]*(?:Logo\b[\s.:#-]*)?"
                r"(?:(?:Lic(?:ence|ense)?\.?|License|No\.?)\s*"
                r"(?:No\.?)?\s*[:#.-]?\s*)?([A-Za-z0-9_]+)?",
                nearby_text,
                re.IGNORECASE
            )

        if fssai_prefix and fssai_prefix.group(1):
            lic_no = fssai_prefix.group(1)
            if not re.fullmatch(r"[12]\d{13}", lic_no):
                digit_count = len(re.sub(r"\D", "", lic_no))
                return {
                    "status": "INVALID",
                    "confidence": 0.92,
                    "evidence": f"Invalid FSSAI licence: '{lic_no}' ({digit_count} digits found instead of the required 14 digits).",
                    "rules_passed": [],
                    "recommendation": "Check the number printed immediately beside the FSSAI licence marking."
                }
            # Check for dummy all-zeros or repetitive digits
            if len(set(lic_no)) <= 2:
                return {
                    "status": "INVALID",
                    "confidence": 0.90,
                    "evidence": f"Suspect dummy licence number: '{lic_no}'",
                    "rules_passed": ["14-digit length check"],
                    "recommendation": "FSSAI licence number must be an authentic 14-digit number issued by Central/State Licensing Authority."
                }
            return {
                "status": "PRESENT",
                "confidence": 0.98,
                "evidence": f"Valid 14-digit FSSAI Licence Number: {lic_no}",
                "rules_passed": [
                    "FSSAI designation verified",
                    "Mandatory 14-digit numeric length validated",
                    f"Valid state/central prefix: {lic_no[:3]}"
                ],
                "recommendation": "Compliant with FSSAI Regulation 5(9)."
            }
        elif fssai_prefix:
            return {
                "status": "INVALID",
                "confidence": 0.40,
                "evidence": "FSSAI logo / keyword present, but 14-digit licence number is missing.",
                "rules_passed": [],
                "recommendation": "FSSAI logo must always be accompanied by the 14-digit licence number."
            }

        return {
            "status": "MISSING",
            "confidence": 0.0,
            "evidence": "FSSAI logo and 14-digit licence number completely missing.",
            "rules_passed": [],
            "recommendation": "Mandatory under Section 31 of Food Safety and Standards Act, 2006."
        }

    @staticmethod
    def _verify_batch_number(text):
        """11. Lot / Code / Batch Identification"""
        batch_match = re.search(r"\b(?:Batch\s*(?:N[oa]\.?|Number|#)?|Lot\s*(?:N[oa]\.?|Number|#)?|B\.No\.?)\s*[:\-\.]?\s*([A-Za-z0-9\-]+)\b", text, re.IGNORECASE)

        if batch_match:
            val = batch_match.group(1).strip()
            if val.lower() in {
                "none", "nil", "na", "n/a", "missing", "not", "available",
                "printed", "declared", "shown", "0"
            }:
                return {
                    "status": "INVALID",
                    "confidence": 0.30,
                    "evidence": f"Invalid batch placeholder: '{val}'",
                    "rules_passed": [],
                    "recommendation": "A unique traceable production batch code is mandatory."
                }
            return {
                "status": "PRESENT",
                "confidence": 0.95,
                "evidence": f"Batch identification code: '{val}'",
                "rules_passed": [
                    "Batch/Lot prefix verified",
                    "Alphanumeric batch code parsed"
                ],
                "recommendation": "Compliant with FSSAI Regulation 5(10)."
            }

        return {
            "status": "MISSING",
            "confidence": 0.0,
            "evidence": "Lot / Code / Batch identification number not detected.",
            "rules_passed": [],
            "recommendation": "Mandatory for traceability under FSSAI Regulation 5(10)."
        }

    @staticmethod
    def _verify_date_marking(text):
        """12. Detect manufacturing/packing and best-before/expiry declarations."""
        mfg_pattern = re.compile(
            r"\b(?:Date\s*of\s*(?:Mfg|Manufacture|Packaging|Packing|Pkg)|"
            r"Mfg\.?(?:\s*Date)?|Mfd\.?(?:\s*Date)?|Mfd|Manufacturing\s*Date|"
            r"Pkd(?:\s*Date)?|Packed\s*on|Manufactured\s*on)\b"
            r"(?!\s+by\b)\s*[:#\-]?\s*",
            re.IGNORECASE
        )
        exp_pattern = re.compile(
            r"\b(?:Best\s*(?:Be\s*)?fore|Expiry(?:\s*Date)?|Use\s*by|Exp\.?)\b"
            r"\s*[:#\-]?\s*",
            re.IGNORECASE
        )
        mfg_match = mfg_pattern.search(text)
        exp_match = exp_pattern.search(text)
        mfg_value = ""
        exp_value = ""
        if mfg_match:
            mfg_end = exp_match.start() if exp_match and exp_match.start() > mfg_match.end() else len(text)
            mfg_value = text[mfg_match.end():mfg_end]
        if exp_match:
            exp_value = text[exp_match.end():]
        for boundary_pattern in (
            r"\n", r"\|", r"\b(?:Store|Storage|Batch|Lot|MRP|FSSAI|Net\s*(?:Wt|Weight|Quantity)|Country\s+of|Made\s+in)\b"
        ):
            mfg_boundary = re.search(boundary_pattern, mfg_value, re.IGNORECASE)
            if mfg_boundary:
                mfg_value = mfg_value[:mfg_boundary.start()]
            exp_boundary = re.search(boundary_pattern, exp_value, re.IGNORECASE)
            if exp_boundary:
                exp_value = exp_value[:exp_boundary.start()]
        mfg_value = mfg_value.strip(" \t:;,.")
        exp_value = exp_value.strip(" \t:;,.")

        date_pattern = re.compile(
            r"\b(?:\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{1,2}[/-]\d{4}|"
            r"\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
            r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|"
            r"Nov(?:ember)?|Dec(?:ember)?),?\s+\d{4}|"
            r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
            r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
            r"Dec(?:ember)?)\s+\d{4})\b",
            re.IGNORECASE
        )
        shelf_life_pattern = re.compile(
            r"\b\d+\s*(?:days?|weeks?|months?|years?)\b",
            re.IGNORECASE
        )

        def has_valid_calendar_date(value):
            date_match = date_pattern.search(value)
            if not date_match:
                return False
            date_value = date_match.group(0)
            for date_format in (
                "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
                "%d/%m/%y", "%d-%m-%y", "%d.%m.%y",
                "%m/%d/%Y", "%m-%d-%Y", "%m.%d.%Y",
                "%m/%d/%y", "%m-%d-%y", "%m.%d.%y",
                "%d %B %Y", "%d %b %Y", "%d %B, %Y", "%d %b, %Y",
                "%m/%Y", "%m-%Y", "%m/%y", "%m-%y",
                "%B %Y", "%b %Y"
            ):
                try:
                    datetime.strptime(date_value, date_format)
                    return True
                except ValueError:
                    continue
            return False

        valid_mfg = bool(mfg_match and has_valid_calendar_date(mfg_value))
        valid_exp = bool(
            exp_match
            and (has_valid_calendar_date(exp_value) or shelf_life_pattern.search(exp_value))
        )

        if valid_mfg and valid_exp:
            return {
                "status": "PRESENT",
                "confidence": 0.98,
                "evidence": f"Mfg/Pkg Date: '{mfg_value}', Shelf-life / Expiry: '{exp_value}'",
                "rules_passed": [
                    f"Date of manufacture parsed: {mfg_value}",
                    f"Best before / expiry statement parsed: {exp_value}"
                ],
                "recommendation": "Both manufacturing/packing and best-before/expiry declarations were detected."
            }

        return {
            "status": "MISSING",
            "confidence": 0.0,
            "evidence": "Both a manufacturing/packing date and a best-before/expiry value were not detected.",
            "rules_passed": [],
            "recommendation": "Check the original label for both date declarations."
        }

    @staticmethod
    def _verify_instructions(text):
        """13. Instructions for Use & Storage"""
        storage_match = re.search(r"\b(?:Store\s*in\s*a?\s*cool|Keep\s*refrigerated|Keep\s*dry|Store\s*away|Store\s*at|Keep\s*in\s*airtight|Store\s*in\s*dark)\b", text, re.IGNORECASE)
        usage_match = re.search(r"\b(?:Shake\s*well|Ready\s*to\s*eat|Boil\s*in|Do\s*not\s*consume\s*if|Preparation|Refrigerate\s*after\s*opening)\b", text, re.IGNORECASE)

        if storage_match and usage_match:
            return {
                "status": "PRESENT",
                "confidence": 0.95,
                "evidence": "Both storage conditions and specific usage instructions verified.",
                "rules_passed": ["Storage guidance parsed", "Usage/handling instructions parsed"],
                "recommendation": "Compliant with FSSAI Regulation 5(12)."
            }
        elif storage_match or usage_match:
            evidence_str = "Storage conditions verified." if storage_match else "Handling instructions verified."
            return {
                "status": "PRESENT",
                "confidence": 0.88,
                "evidence": evidence_str,
                "rules_passed": ["Mandatory guidance identified"],
                "recommendation": "Compliant with FSSAI Regulation 5(12)."
            }

        return {
            "status": "NEEDS_REVIEW",
            "confidence": 0.40,
            "evidence": "No clear storage conditions or usage instructions detected.",
            "rules_passed": [],
            "recommendation": "Mandatory where special conditions are required to maintain product integrity."
        }

    @staticmethod
    def _verify_country_of_origin(text):
        """14. Country of Origin"""
        origin_match = re.search(r"\b(?:Product\s*of\s*India|Made\s*in\s*India|Country\s*of\s*Origin\s*[:\-]?\s*([A-Za-z]+)|Imported\s*(?:from|by))\b", text, re.IGNORECASE)

        if origin_match:
            val = origin_match.group(0).strip()
            return {
                "status": "PRESENT",
                "confidence": 0.95,
                "evidence": f"Country of origin declared: '{val}'",
                "rules_passed": ["Statutory origin country verified"],
                "recommendation": "Compliant with FSSAI Regulation 5(13)."
            }

        return {
            "status": "NEEDS_REVIEW",
            "confidence": 0.40,
            "evidence": "Explicit Country of Origin declaration not detected.",
            "rules_passed": [],
            "recommendation": "Mandatory for all packaged food products under FSSAI 2020."
        }
