"""PDF extraction and parsing using pdfplumber."""
import pdfplumber
import re
import json
import os


def extract_text_from_pdf(filepath):
    """Extract all text from a PDF file."""
    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""
    return text.strip()


def parse_blood_report(text):
    """Parse blood test report text into structured data."""
    results = {
        "patient_info": {},
        "test_results": [],
        "summary": "",
        "raw_text": text
    }

    # Try to extract patient info
    name_match = re.search(r"(?:Patient\s*Name|Name)\s*[:\-]\s*(.+)", text, re.IGNORECASE)
    if name_match:
        results["patient_info"]["name"] = name_match.group(1).strip()

    age_match = re.search(r"(?:Age)\s*[:\-]\s*(\d+)", text, re.IGNORECASE)
    if age_match:
        results["patient_info"]["age"] = age_match.group(1).strip()

    gender_match = re.search(r"(?:Gender|Sex)\s*[:\-]\s*(\w+)", text, re.IGNORECASE)
    if gender_match:
        results["patient_info"]["gender"] = gender_match.group(1).strip()

    date_match = re.search(r"(?:Date|Report\s*Date|Collection\s*Date)\s*[:\-]\s*(.+)", text, re.IGNORECASE)
    if date_match:
        results["patient_info"]["date"] = date_match.group(1).strip()

    # Parse lab values - look for patterns like "Test Name  Value  Unit  Reference Range"
    lab_patterns = [
        # Pattern: Test Name ... Value Unit (Ref: low-high)
        r"([A-Za-z\s\(\)]+?)\s+([\d\.]+)\s*(mg/dL|g/dL|%|mmol/L|mEq/L|U/L|IU/L|cells/cumm|million/cumm|fl|pg|g%|mm/hr|lakhs/cumm|thou/cumm)\s*(?:[\(\[]?\s*([\d\.]+-[\d\.]+)\s*[\)\]]?)?",
    ]

    common_tests = {
        "Hemoglobin": {"unit": "g/dL", "ref_low": 12.0, "ref_high": 17.5, "category": "Hematology"},
        "RBC Count": {"unit": "million/cumm", "ref_low": 4.5, "ref_high": 5.5, "category": "Hematology"},
        "WBC Count": {"unit": "cells/cumm", "ref_low": 4000, "ref_high": 11000, "category": "Hematology"},
        "Platelet Count": {"unit": "lakhs/cumm", "ref_low": 1.5, "ref_high": 4.0, "category": "Hematology"},
        "PCV": {"unit": "%", "ref_low": 36, "ref_high": 46, "category": "Hematology"},
        "MCV": {"unit": "fl", "ref_low": 83, "ref_high": 101, "category": "Hematology"},
        "MCH": {"unit": "pg", "ref_low": 27, "ref_high": 32, "category": "Hematology"},
        "MCHC": {"unit": "g/dL", "ref_low": 31.5, "ref_high": 34.5, "category": "Hematology"},
        "Blood Glucose Fasting": {"unit": "mg/dL", "ref_low": 70, "ref_high": 100, "category": "Biochemistry"},
        "Blood Glucose PP": {"unit": "mg/dL", "ref_low": 70, "ref_high": 140, "category": "Biochemistry"},
        "HbA1c": {"unit": "%", "ref_low": 4.0, "ref_high": 5.6, "category": "Biochemistry"},
        "Total Cholesterol": {"unit": "mg/dL", "ref_low": 0, "ref_high": 200, "category": "Lipid Profile"},
        "HDL Cholesterol": {"unit": "mg/dL", "ref_low": 40, "ref_high": 60, "category": "Lipid Profile"},
        "LDL Cholesterol": {"unit": "mg/dL", "ref_low": 0, "ref_high": 100, "category": "Lipid Profile"},
        "Triglycerides": {"unit": "mg/dL", "ref_low": 0, "ref_high": 150, "category": "Lipid Profile"},
        "VLDL": {"unit": "mg/dL", "ref_low": 5, "ref_high": 40, "category": "Lipid Profile"},
        "Creatinine": {"unit": "mg/dL", "ref_low": 0.7, "ref_high": 1.3, "category": "Renal Profile"},
        "Blood Urea": {"unit": "mg/dL", "ref_low": 15, "ref_high": 45, "category": "Renal Profile"},
        "Uric Acid": {"unit": "mg/dL", "ref_low": 3.5, "ref_high": 7.2, "category": "Renal Profile"},
        "Bilirubin Total": {"unit": "mg/dL", "ref_low": 0.1, "ref_high": 1.2, "category": "Liver Profile"},
        "SGOT": {"unit": "U/L", "ref_low": 5, "ref_high": 40, "category": "Liver Profile"},
        "SGPT": {"unit": "U/L", "ref_low": 7, "ref_high": 56, "category": "Liver Profile"},
        "Alkaline Phosphatase": {"unit": "U/L", "ref_low": 44, "ref_high": 147, "category": "Liver Profile"},
        "Total Protein": {"unit": "g/dL", "ref_low": 6.0, "ref_high": 8.3, "category": "Liver Profile"},
        "Albumin": {"unit": "g/dL", "ref_low": 3.5, "ref_high": 5.5, "category": "Liver Profile"},
        "TSH": {"unit": "mIU/L", "ref_low": 0.4, "ref_high": 4.0, "category": "Thyroid Profile"},
        "T3": {"unit": "ng/dL", "ref_low": 80, "ref_high": 200, "category": "Thyroid Profile"},
        "T4": {"unit": "mcg/dL", "ref_low": 4.5, "ref_high": 12.5, "category": "Thyroid Profile"},
        "ESR": {"unit": "mm/hr", "ref_low": 0, "ref_high": 20, "category": "Hematology"},
        "Sodium": {"unit": "mEq/L", "ref_low": 136, "ref_high": 145, "category": "Electrolytes"},
        "Potassium": {"unit": "mEq/L", "ref_low": 3.5, "ref_high": 5.1, "category": "Electrolytes"},
        "Chloride": {"unit": "mEq/L", "ref_low": 98, "ref_high": 106, "category": "Electrolytes"},
        "Calcium": {"unit": "mg/dL", "ref_low": 8.5, "ref_high": 10.5, "category": "Electrolytes"},
        "Iron": {"unit": "mcg/dL", "ref_low": 60, "ref_high": 170, "category": "Hematology"},
        "Vitamin D": {"unit": "ng/mL", "ref_low": 30, "ref_high": 100, "category": "Vitamins"},
        "Vitamin B12": {"unit": "pg/mL", "ref_low": 200, "ref_high": 900, "category": "Vitamins"},
    }

    # Search for known test names in the text
    for test_name, info in common_tests.items():
        # Look for the test name followed by a numeric value
        pattern = re.escape(test_name) + r"\s*[:\-]?\s*([\d\.]+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            status = "Normal"
            if value < info["ref_low"]:
                status = "Low"
            elif value > info["ref_high"]:
                status = "High"

            results["test_results"].append({
                "name": test_name,
                "value": value,
                "unit": info["unit"],
                "ref_low": info["ref_low"],
                "ref_high": info["ref_high"],
                "status": status,
                "category": info["category"]
            })

    # If no structured results found, create a generic entry with the raw text
    if not results["test_results"]:
        # Try a more generic pattern
        generic_pattern = r"([A-Za-z][\w\s\(\)]*?)\s*[:\-]\s*([\d\.]+)\s*([\w/%]+)"
        for match in re.finditer(generic_pattern, text):
            name = match.group(1).strip()
            if len(name) > 3 and len(name) < 40:
                try:
                    value = float(match.group(2))
                    results["test_results"].append({
                        "name": name,
                        "value": value,
                        "unit": match.group(3),
                        "ref_low": None,
                        "ref_high": None,
                        "status": "Unknown",
                        "category": "General"
                    })
                except ValueError:
                    continue

    results["summary"] = f"Found {len(results['test_results'])} test parameters"
    return results


def process_uploaded_pdf(filepath):
    """Full pipeline: extract text -> parse into structured data."""
    text = extract_text_from_pdf(filepath)
    if not text:
        return {
            "patient_info": {},
            "test_results": [],
            "summary": "Could not extract text from PDF",
            "raw_text": ""
        }
    return parse_blood_report(text)
