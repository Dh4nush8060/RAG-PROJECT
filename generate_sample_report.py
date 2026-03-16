"""Generate a sample blood test report PDF for demo purposes."""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
import os

def create_sample_report():
    filepath = os.path.join(os.path.dirname(__file__), "sample_reports", "sample_blood_report.pdf")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle('HospitalName', parent=styles['Heading1'], fontSize=22,
                              textColor=colors.HexColor('#1565c0'), alignment=TA_CENTER, spaceAfter=4))
    styles.add(ParagraphStyle('SubTitle', parent=styles['Normal'], fontSize=11,
                              textColor=colors.grey, alignment=TA_CENTER, spaceAfter=20))

    elements = []

    elements.append(Paragraph("Apollo Hospitals, Chennai", styles['HospitalName']))
    elements.append(Paragraph("Department of Laboratory Medicine | NABL Accredited", styles['SubTitle']))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1565c0'), spaceAfter=15))

    # Patient Info
    info_data = [
        ["Patient Name: Richard Kumar", "Age: 41 Years", "Gender: Male"],
        ["Patient ID: APH-2026-00142", "Collection Date: 28-Feb-2026", "Report Date: 01-Mar-2026"],
        ["Referred By: Dr. S. Venkatesh", "Sample Type: Blood (EDTA/Serum)", ""]
    ]
    info_table = Table(info_data, colWidths=[200, 180, 140])
    info_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 15))

    # Hematology
    elements.append(Paragraph("COMPLETE BLOOD COUNT (CBC)", styles['Heading2']))
    cbc_data = [
        ["Test", "Result", "Unit", "Reference Range"],
        ["Hemoglobin", "11.2", "g/dL", "13.0 - 17.0"],
        ["RBC Count", "4.2", "million/cumm", "4.5 - 5.5"],
        ["WBC Count", "8500", "cells/cumm", "4000 - 11000"],
        ["Platelet Count", "2.8", "lakhs/cumm", "1.5 - 4.0"],
        ["PCV", "38", "%", "40 - 50"],
        ["MCV", "88", "fl", "83 - 101"],
        ["MCH", "29", "pg", "27 - 32"],
        ["MCHC", "33", "g/dL", "31.5 - 34.5"],
        ["ESR", "25", "mm/hr", "0 - 20"],
    ]

    # Biochemistry
    elements.append(create_lab_table(cbc_data))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("BIOCHEMISTRY", styles['Heading2']))
    bio_data = [
        ["Test", "Result", "Unit", "Reference Range"],
        ["Blood Glucose Fasting", "118", "mg/dL", "70 - 100"],
        ["Blood Glucose PP", "165", "mg/dL", "70 - 140"],
        ["HbA1c", "6.8", "%", "4.0 - 5.6"],
        ["Creatinine", "1.1", "mg/dL", "0.7 - 1.3"],
        ["Blood Urea", "35", "mg/dL", "15 - 45"],
        ["Uric Acid", "7.8", "mg/dL", "3.5 - 7.2"],
        ["Bilirubin Total", "0.8", "mg/dL", "0.1 - 1.2"],
        ["SGOT", "28", "U/L", "5 - 40"],
        ["SGPT", "35", "U/L", "7 - 56"],
        ["Alkaline Phosphatase", "85", "U/L", "44 - 147"],
        ["Total Protein", "7.2", "g/dL", "6.0 - 8.3"],
        ["Albumin", "4.1", "g/dL", "3.5 - 5.5"],
    ]
    elements.append(create_lab_table(bio_data))
    elements.append(Spacer(1, 15))

    # Lipid Profile
    elements.append(Paragraph("LIPID PROFILE", styles['Heading2']))
    lipid_data = [
        ["Test", "Result", "Unit", "Reference Range"],
        ["Total Cholesterol", "235", "mg/dL", "0 - 200"],
        ["HDL Cholesterol", "38", "mg/dL", "40 - 60"],
        ["LDL Cholesterol", "155", "mg/dL", "0 - 100"],
        ["Triglycerides", "210", "mg/dL", "0 - 150"],
        ["VLDL", "42", "mg/dL", "5 - 40"],
    ]
    elements.append(create_lab_table(lipid_data))
    elements.append(Spacer(1, 15))

    # Thyroid
    elements.append(Paragraph("THYROID PROFILE", styles['Heading2']))
    thyroid_data = [
        ["Test", "Result", "Unit", "Reference Range"],
        ["TSH", "5.2", "mIU/L", "0.4 - 4.0"],
        ["Vitamin D", "18", "ng/mL", "30 - 100"],
        ["Vitamin B12", "280", "pg/mL", "200 - 900"],
    ]
    elements.append(create_lab_table(thyroid_data))
    elements.append(Spacer(1, 20))

    # Footer
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey, spaceAfter=10))
    elements.append(Paragraph(
        "This is a computer-generated report. Please correlate clinically. "
        "For any queries, contact the laboratory at +91-44-2829-3333.",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
    ))

    doc.build(elements)
    print(f"Sample report created: {filepath}")
    return filepath


def create_lab_table(data):
    table = Table(data, colWidths=[160, 80, 90, 130])
    style_commands = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e3f2fd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1565c0')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bbdefb')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fafafa')]),
    ]

    # Highlight abnormal values
    abnormal_checks = {
        "Hemoglobin": (13.0, 17.0), "RBC Count": (4.5, 5.5), "ESR": (0, 20),
        "PCV": (40, 50), "Blood Glucose Fasting": (70, 100), "Blood Glucose PP": (70, 140),
        "HbA1c": (4.0, 5.6), "Uric Acid": (3.5, 7.2),
        "Total Cholesterol": (0, 200), "HDL Cholesterol": (40, 60),
        "LDL Cholesterol": (0, 100), "Triglycerides": (0, 150), "VLDL": (5, 40),
        "TSH": (0.4, 4.0), "Vitamin D": (30, 100),
    }

    for i, row in enumerate(data[1:], 1):
        test_name = row[0]
        if test_name in abnormal_checks:
            try:
                val = float(row[1])
                low, high = abnormal_checks[test_name]
                if val < low or val > high:
                    style_commands.append(('TEXTCOLOR', (1, i), (1, i), colors.HexColor('#d32f2f')))
                    style_commands.append(('FONTNAME', (1, i), (1, i), 'Helvetica-Bold'))
            except ValueError:
                pass

    table.setStyle(TableStyle(style_commands))
    return table


if __name__ == "__main__":
    create_sample_report()
