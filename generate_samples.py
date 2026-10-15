"""
Realistic Food Label Image Generator
AI-Based Food Label Compliance Verification Platform

Generates 4 high-resolution food label sample images with authentic FSSAI markings:
1. sample_snack_pack.png (Compliant Snack Label)
2. sample_mango_juice.png (Compliant Beverage Label)
3. sample_masala_pouch.png (Partially Compliant Spice Label)
4. sample_defective_label.png (Non-Compliant Defective Label)
"""

import os
from PIL import Image, ImageDraw, ImageFont

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "static", "sample_images")
os.makedirs(SAMPLE_DIR, exist_ok=True)


def draw_fssai_veg_logo(draw, x, y, size=36, is_veg=True):
    """Draws authentic statutory FSSAI Veg (Green dot) or Non-Veg (Brown triangle) logo."""
    # Outer square border
    color = (34, 139, 34) if is_veg else (139, 34, 34)
    draw.rectangle([x, y, x + size, y + size], outline=color, width=3)
    
    # Inner shape
    padding = size // 5
    if is_veg:
        # Green filled circle
        draw.ellipse([x + padding, y + padding, x + size - padding, y + size - padding], fill=color)
    else:
        # Brown filled triangle
        p1 = (x + size // 2, y + padding)
        p2 = (x + padding, y + size - padding)
        p3 = (x + size - padding, y + size - padding)
        draw.polygon([p1, p2, p3], fill=color)


def create_sample_snack_pack():
    """1. Fully Compliant Potato Chips Label"""
    img = Image.new("RGB", (700, 950), color=(252, 250, 242))
    draw = ImageDraw.Draw(img)

    # Header Banner
    draw.rectangle([0, 0, 700, 90], fill=(211, 47, 47))
    draw.text((30, 25), "CRISP KRAFT POTATO CHIPS - SPICY MASALA", fill=(255, 255, 255))
    
    # Veg Logo
    draw_fssai_veg_logo(draw, 620, 26, size=40, is_veg=True)

    y = 110
    lines = [
        "Ingredients: Potatoes (64%), Edible Vegetable Oil (Palmolein), Spices & Condiments",
        "(Chilli, Coriander, Cumin, Amchur, Black Pepper), Iodised Salt, Acidity Regulator (INS 330),",
        "Flavour Enhancers (INS 627, INS 631). Contains Added Flavours (Natural & Nature Identical).",
        "",
        "NUTRITIONAL INFORMATION (Per 100g Approx):",
        "----------------------------------------------------------------------------------",
        "Energy: 540 kcal  |  Protein: 6.8 g  |  Carbohydrates: 52 g",
        "Total Sugars: 2.1 g  |  Added Sugars: 0.0 g  |  Total Fat: 34 g",
        "Saturated Fat: 15.2 g  |  Trans Fat: 0.1 g  |  Sodium: 780 mg",
        "----------------------------------------------------------------------------------",
        "",
        "Vegetarian Logo (Green Circle inside Green Square) Verified",
        "",
        "Manufactured by: Crisp Kraft Snacks Pvt Ltd,",
        "Plot 18, GIDC Industrial Estate, Sanand, Ahmedabad, Gujarat - 382110",
        "",
        "Customer Care: 1800-200-5544  |  Email: care@crispkraft.in",
        "Consumer Grievance Cell at the Registered Office Address above.",
        "",
        "Net Quantity: 115 g",
        "MRP: Rs. 40.00 (inclusive of all taxes)",
        "",
        "FSSAI Lic. No. 10017042001923",
        "Batch No: SPK8812",
        "Date of Packaging: 15/09/2026",
        "Best Before 4 months from packaging",
        "",
        "Storage Instructions: Store in a cool and dry place away from direct sunlight.",
        "Country of Origin: India"
    ]

    for line in lines:
        if "NUTRITIONAL" in line or "FSSAI" in line:
            draw.text((35, y), line, fill=(183, 28, 28))
        else:
            draw.text((35, y), line, fill=(33, 33, 33))
        y += 26

    # Bottom accent
    draw.rectangle([0, 930, 700, 950], fill=(211, 47, 47))
    out_path = os.path.join(SAMPLE_DIR, "sample_snack_pack.png")
    img.save(out_path)
    print(f"Generated: {out_path}")


def create_sample_mango_juice():
    """2. Fully Compliant Mango Nectar Label"""
    img = Image.new("RGB", (700, 950), color=(255, 252, 235))
    draw = ImageDraw.Draw(img)

    # Header
    draw.rectangle([0, 0, 700, 90], fill=(245, 124, 0))
    draw.text((30, 25), "TROPIC PURE ALPHONSO MANGO NECTAR", fill=(255, 255, 255))
    
    # Veg Logo
    draw_fssai_veg_logo(draw, 620, 26, size=40, is_veg=True)

    y = 110
    lines = [
        "Ingredients: Water, Alphonso Mango Pulp (45%), Sugar, Acidity Regulator (INS 330),",
        "Antioxidant (INS 300). Contains Permitted Natural Colour & Added Mango Flavours.",
        "",
        "NUTRITION INFORMATION (Per 100ml):",
        "----------------------------------------------------------------------------------",
        "Energy: 62 kcal  |  Protein: 0.3 g  |  Carbohydrates: 15 g",
        "Total Sugars: 14.2 g  |  Added Sugars: 9.5 g  |  Total Fat: 0.1 g",
        "Saturated Fat: 0 g  |  Trans Fat: 0 g  |  Sodium: 15 mg",
        "----------------------------------------------------------------------------------",
        "",
        "Vegetarian Symbol Declared",
        "",
        "Manufactured & Packed by: Tropic Foods India Ltd,",
        "NH-8, Industrial Area, Vapi, Gujarat - 396195",
        "",
        "Customer Support: 1800-102-2244  |  Email: feedback@tropicanaindia.com",
        "Grievance Officer Address: Tropic Foods India Ltd, NH-8, Vapi, Gujarat - 396195",
        "",
        "Net Volume: 1 L",
        "MRP: Rs. 110.00 (inclusive of all taxes)",
        "",
        "FSSAI Lic. No. 10014021000888",
        "Lot No: MN2026B",
        "Date of Packaging: 01/10/2026",
        "Best Before 6 months from packaging",
        "",
        "Instructions: Shake well before use. Store in cool hygienic place.",
        "Refrigerate after opening and consume within 5 days.",
        "Made in India"
    ]

    for line in lines:
        if "NUTRITION" in line or "FSSAI" in line:
            draw.text((35, y), line, fill=(230, 81, 0))
        else:
            draw.text((35, y), line, fill=(33, 33, 33))
        y += 26

    draw.rectangle([0, 930, 700, 950], fill=(245, 124, 0))
    out_path = os.path.join(SAMPLE_DIR, "sample_mango_juice.png")
    img.save(out_path)
    print(f"Generated: {out_path}")


def create_sample_masala_pouch():
    """3. Partially Compliant Spice Label (Minor omissions)"""
    img = Image.new("RGB", (700, 950), color=(253, 248, 245))
    draw = ImageDraw.Draw(img)

    # Header
    draw.rectangle([0, 0, 700, 90], fill=(142, 36, 170))
    draw.text((30, 25), "ROYAL MALABAR SPECIAL GARAM MASALA", fill=(255, 255, 255))
    
    # Veg Logo
    draw_fssai_veg_logo(draw, 620, 26, size=40, is_veg=True)

    y = 110
    lines = [
        "Ingredients: Coriander Seeds, Cumin, Black Pepper, Cardamom, Cinnamon, Cloves, Star Anise.",
        "",
        "NUTRITION FACTS (Per 100g):",
        "----------------------------------------------------------------------------------",
        "Energy: 360 kcal  |  Protein: 12 g  |  Carbohydrates: 45 g  |  Fat: 14 g",
        "(Notice: Sugars, Saturated Fat, Trans Fat, and Sodium breakdown not declared)",
        "----------------------------------------------------------------------------------",
        "",
        "Green Vegetarian Logo Present",
        "",
        "Packed by: Malabar Spice Mills,",
        "Spice Complex, Willingdon Island, Kochi, Kerala - 682003",
        "",
        "Customer Care Helpline: 0484-2667788",
        "(Customer care email address omitted)",
        "",
        "Net Wt: 200 g",
        "MRP: Rs. 145.00 (inclusive of all taxes)",
        "",
        "FSSAI Lic. No. 11316007000199",
        "Batch: GM-882",
        "Date of Packing: 05/10/2026",
        "Best Before 12 months from packing",
        "",
        "Keep in a cool dry place.",
        "Country of Origin: India"
    ]

    for line in lines:
        if "NUTRITION" in line or "FSSAI" in line:
            draw.text((35, y), line, fill=(106, 27, 154))
        else:
            draw.text((35, y), line, fill=(33, 33, 33))
        y += 28

    draw.rectangle([0, 930, 700, 950], fill=(142, 36, 170))
    out_path = os.path.join(SAMPLE_DIR, "sample_masala_pouch.png")
    img.save(out_path)
    print(f"Generated: {out_path}")


def create_sample_defective_label():
    """4. Non-Compliant Defective Food Label (Major FSSAI Violations)"""
    img = Image.new("RGB", (700, 950), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)

    # Header
    draw.rectangle([0, 0, 700, 90], fill=(69, 90, 100))
    draw.text((30, 25), "DELICIOUS BUTTER COOKIES (DEFECTIVE DEMO)", fill=(255, 255, 255))
    
    # Missing Veg Logo! (Empty area with X)
    draw.rectangle([615, 20, 665, 70], outline=(255, 82, 82), width=2)
    draw.line([615, 20, 665, 70], fill=(255, 82, 82), width=2)
    draw.line([615, 70, 665, 20], fill=(255, 82, 82), width=2)

    y = 110
    lines = [
        "Ingredients: Refined Wheat Flour, Sugar, Butter, Artificial Flavours.",
        "",
        "[VIOLATION 1: Nutritional Information table is completely missing!]",
        "",
        "[VIOLATION 2: Mandatory Green Veg Dot or Brown Non-Veg symbol is ABSENT!]",
        "",
        "Manufactured by: Sweet Bakers, City Area",
        "[VIOLATION 3: Incomplete address - No registered premises, state or PIN code]",
        "",
        "Customer Care: None",
        "[VIOLATION 4: No helpline phone, email, or grievance address provided]",
        "",
        "Net Quantity: 200",
        "[VIOLATION 5: Unit omitted - Legal Metrology requires grams or kilograms]",
        "",
        "Price: Rs 50",
        "[VIOLATION 6: Mandatory 'inclusive of all taxes' statement missing]",
        "",
        "FSSAI License: 12345678",
        "[VIOLATION 7: INVALID LICENSE - Only 8 digits instead of mandatory 14 digits!]",
        "",
        "Batch: None",
        "[VIOLATION 8: Batch identification code absent]",
        "",
        "Mfg Date: 2026",
        "[VIOLATION 9: Expiry / Best Before date completely missing]",
        "",
        "Keep cool",
        "[VIOLATION 10: Country of Origin not declared]"
    ]

    for line in lines:
        if "VIOLATION" in line:
            draw.text((35, y), line, fill=(198, 40, 40))
        else:
            draw.text((35, y), line, fill=(66, 66, 66))
        y += 28

    draw.rectangle([0, 930, 700, 950], fill=(69, 90, 100))
    out_path = os.path.join(SAMPLE_DIR, "sample_defective_label.png")
    img.save(out_path)
    print(f"Generated: {out_path}")


if __name__ == "__main__":
    create_sample_snack_pack()
    create_sample_mango_juice()
    create_sample_masala_pouch()
    create_sample_defective_label()
    print("All 4 sample food label images generated successfully.")
