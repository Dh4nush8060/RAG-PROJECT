"""PDF report generator using ReportLab."""
import io
import json
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def generate_patient_report_pdf(patient_info, report_data, ai_explanation, diet_plan, insights):
    """Generate a comprehensive patient-friendly PDF report."""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=12,
        alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#283593'),
        spaceBefore=20,
        spaceAfter=10,
        borderPadding=(0, 0, 5, 0)
    ))
    styles.add(ParagraphStyle(
        'SubSection',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=colors.HexColor('#3949ab'),
        spaceBefore=12,
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        'BodyText2',
        parent=styles['BodyText'],
        fontSize=10,
        leading=14,
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        'SmallText',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey
    ))

    elements = []

    # ---- Header ----
    elements.append(Paragraph("🏥 MedExplain AI", styles['ReportTitle']))
    elements.append(Paragraph("Your Personalized Health Report", ParagraphStyle(
        'Subtitle', parent=styles['Normal'], fontSize=14,
        textColor=colors.HexColor('#5c6bc0'), alignment=TA_CENTER, spaceAfter=20
    )))
    elements.append(HRFlowable(
        width="100%", thickness=2, color=colors.HexColor('#3f51b5'),
        spaceAfter=15
    ))

    # ---- Patient Info ----
    elements.append(Paragraph("📋 Patient Information", styles['SectionTitle']))
    p_info = patient_info or {}
    info_data = [
        ["Name", p_info.get("name", "N/A"), "Date", datetime.now().strftime("%d %b %Y")],
        ["Gender", p_info.get("gender", "N/A"), "Blood Group", p_info.get("blood_group", "N/A")],
    ]
    info_table = Table(info_data, colWidths=[80, 180, 80, 180])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8eaf6')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#e8eaf6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1a237e')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#c5cae9')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 15))

    # ---- Health Score ----
    if insights and insights.get("overall_score") is not None:
        elements.append(Paragraph("🎯 Overall Health Score", styles['SectionTitle']))
        score = insights["overall_score"]
        status = insights.get("overall_status", "N/A")
        score_color = '#4caf50' if score >= 80 else '#ff9800' if score >= 60 else '#f44336'
        elements.append(Paragraph(
            f'<font size="28" color="{score_color}"><b>{score}%</b></font> '
            f'<font size="14" color="#666"> — {status}</font>',
            ParagraphStyle('Score', parent=styles['Normal'], alignment=TA_CENTER, spaceAfter=15)
        ))

    # ---- Test Results Table ----
    test_results = report_data.get("test_results", []) if isinstance(report_data, dict) else []
    if test_results:
        elements.append(Paragraph("🔬 Lab Test Results", styles['SectionTitle']))

        table_data = [["Test Name", "Your Value", "Unit", "Normal Range", "Status"]]
        for test in test_results:
            ref_range = f"{test.get('ref_low', '?')} - {test.get('ref_high', '?')}" if test.get('ref_low') is not None else "N/A"
            status = test['status']
            table_data.append([
                test['name'],
                str(test['value']),
                test['unit'],
                ref_range,
                status
            ])

        result_table = Table(table_data, colWidths=[140, 80, 70, 100, 70])
        style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#283593')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#c5cae9')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]

        # Color code status column
        for i, test in enumerate(test_results, 1):
            if test['status'] == 'High':
                style_commands.append(('TEXTCOLOR', (4, i), (4, i), colors.HexColor('#e65100')))
                style_commands.append(('FONTNAME', (4, i), (4, i), 'Helvetica-Bold'))
            elif test['status'] == 'Low':
                style_commands.append(('TEXTCOLOR', (4, i), (4, i), colors.HexColor('#c62828')))
                style_commands.append(('FONTNAME', (4, i), (4, i), 'Helvetica-Bold'))
            elif test['status'] == 'Normal':
                style_commands.append(('TEXTCOLOR', (4, i), (4, i), colors.HexColor('#2e7d32')))

        result_table.setStyle(TableStyle(style_commands))
        elements.append(result_table)
        elements.append(Spacer(1, 15))

    # ---- AI Explanation ----
    if ai_explanation:
        elements.append(Paragraph("🤖 AI-Powered Report Explanation", styles['SectionTitle']))
        # Clean markdown formatting for PDF
        clean_text = ai_explanation.replace("##", "").replace("**", "").replace("*", "")
        for para in clean_text.split("\n\n"):
            para = para.strip()
            if para:
                elements.append(Paragraph(para, styles['BodyText2']))
        elements.append(Spacer(1, 10))

    # ---- Diet Plan ----
    if diet_plan:
        if isinstance(diet_plan, str):
            try:
                diet_plan = json.loads(diet_plan)
            except:
                diet_plan = {}

        if diet_plan.get("recommendations"):
            elements.append(Paragraph("🍎 Diet Recommendations", styles['SectionTitle']))
            for rec in diet_plan["recommendations"]:
                elements.append(Paragraph(
                    f'<b>{rec.get("icon", "•")} {rec["title"]}</b>: {rec["description"]}',
                    styles['BodyText2']
                ))

        if diet_plan.get("foods_to_include"):
            elements.append(Paragraph("✅ Foods to Include", styles['SubSection']))
            elements.append(Paragraph(
                " • ".join(diet_plan["foods_to_include"]),
                styles['BodyText2']
            ))

        if diet_plan.get("foods_to_avoid"):
            elements.append(Paragraph("❌ Foods to Avoid", styles['SubSection']))
            elements.append(Paragraph(
                " • ".join(diet_plan["foods_to_avoid"]),
                styles['BodyText2']
            ))

        if diet_plan.get("meal_plan"):
            elements.append(Paragraph("🍽️ Sample Meal Plan", styles['SubSection']))
            meal_data = [[k.replace("_", " ").title(), v] for k, v in diet_plan["meal_plan"].items()]
            meal_table = Table(meal_data, colWidths=[120, 380])
            meal_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f5e9')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#c8e6c9')),
            ]))
            elements.append(meal_table)

    elements.append(Spacer(1, 20))

    # ---- Disclaimer ----
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey, spaceAfter=10))
    elements.append(Paragraph(
        "⚕️ <b>Disclaimer:</b> This report is generated by an AI assistant for educational purposes only. "
        "It is NOT a substitute for professional medical advice, diagnosis, or treatment. "
        "Always consult your doctor for medical decisions.",
        ParagraphStyle('Disclaimer', parent=styles['Normal'], fontSize=8,
                       textColor=colors.HexColor('#666'), leading=10)
    ))
    elements.append(Paragraph(
        f"Generated on {datetime.now().strftime('%d %B %Y at %I:%M %p')} by MedExplain AI",
        styles['SmallText']
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer
