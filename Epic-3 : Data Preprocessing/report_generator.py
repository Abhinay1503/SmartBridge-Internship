import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf_report(prediction):
    """
    Generates a PDF report for a single prediction and returns the bytes.
    prediction: an object or dict containing prediction features, date, result, etc.
    """
    buffer = io.BytesIO()
    
    # Page setup
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=colors.HexColor('#1f3b68'),
        spaceAfter=15
    )
    
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#6c757d'),
        spaceAfter=15
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#1f3b68'),
        spaceBefore=10,
        spaceAfter=10,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#212529')
    )
    
    table_text_style = ParagraphStyle(
        'TableText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=11
    )
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.white
    )

    # 1. Header Section
    story.append(Paragraph("FLOOD PREDICTION REPORT", title_style))
    date_str = prediction.date.strftime("%Y-%m-%d %H:%M:%S") if hasattr(prediction, 'date') and isinstance(prediction.date, datetime) else str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    region = prediction.region if hasattr(prediction, 'region') else 'Selected Location'
    story.append(Paragraph(f"<b>Generated On:</b> {date_str} | <b>Target Region:</b> {region}", meta_style))
    story.append(Spacer(1, 10))
    
    # 2. Risk Banner Section
    prob_percentage = (prediction.probability * 100) if hasattr(prediction, 'probability') else 0.0
    risk_level = prediction.risk_level if hasattr(prediction, 'risk_level') else 'Low'
    bg_color = prediction.color if hasattr(prediction, 'color') else '#28a745'
    
    banner_data = [
        [
            Paragraph(f"<font color='white' size='14'><b>PREDICTION RESULT:</b></font>", table_header_style),
            Paragraph(f"<font color='white' size='18'><b>{'FLOOD LIKELY' if (prediction.prediction_label == 1) else 'NO FLOOD'}</b></font>", table_header_style)
        ],
        [
            Paragraph(f"<font color='white'>Probability:</font>", table_header_style),
            Paragraph(f"<font color='white' size='14'><b>{prob_percentage:.2f}%</b></font>", table_header_style)
        ],
        [
            Paragraph(f"<font color='white'>Assessed Risk Level:</font>", table_header_style),
            Paragraph(f"<font color='white' size='14'><b>{risk_level.upper()} RISK</b></font>", table_header_style)
        ]
    ]
    
    banner_table = Table(banner_data, colWidths=[200, 340])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg_color)),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 15),
        ('RIGHTPADDING', (0,0), (-1,-1), 15),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor(bg_color))
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 20))
    
    # 3. Action Recommendations
    story.append(Paragraph("Emergency & Precautionary Recommendations", section_title_style))
    rec_text = prediction.recommendation if hasattr(prediction, 'recommendation') else "Monitor standard regional updates."
    story.append(Paragraph(rec_text, body_style))
    story.append(Spacer(1, 15))
    
    # 4. Meteorological Input Parameters Table
    story.append(Paragraph("Input Meteorological & Geographic Parameters", section_title_style))
    
    # Format data for table
    raw_inputs = [
        ("Annual Rainfall", f"{prediction.annual_rainfall:.1f} mm", "Monsoon Rainfall", f"{prediction.monsoon_rainfall:.1f} mm"),
        ("Winter Rainfall", f"{prediction.winter_rainfall:.1f} mm", "Summer Rainfall", f"{prediction.summer_rainfall:.1f} mm"),
        ("Relative Humidity", f"{prediction.relative_humidity:.1f} %", "Temperature", f"{prediction.temperature:.1f} °C"),
        ("Cloud Cover", f"{prediction.cloud_cover:.1f} octas", "Cloud Visibility", f"{prediction.cloud_visibility:.1f} km"),
        ("River Water Level", f"{prediction.river_water_level:.2f} m", "Soil Moisture", f"{prediction.soil_moisture:.1f} %"),
        ("Wind Speed", f"{prediction.wind_speed:.1f} km/h", "Atmospheric Pressure", f"{prediction.atmospheric_pressure:.1f} hPa"),
        ("Drainage Density", f"{prediction.drainage_density:.2f} km/km²", "Elevation", f"{prediction.elevation:.1f} m"),
        ("Previous Flood History", "Yes" if prediction.previous_flood_history == 1 else "No", "", "")
    ]
    
    table_data = [
        [
            Paragraph("<b>Parameter</b>", table_header_style), 
            Paragraph("<b>Value</b>", table_header_style),
            Paragraph("<b>Parameter</b>", table_header_style), 
            Paragraph("<b>Value</b>", table_header_style)
        ]
    ]
    
    for row in raw_inputs:
        table_data.append([
            Paragraph(row[0], table_text_style),
            Paragraph(row[1], table_text_style),
            Paragraph(row[2], table_text_style),
            Paragraph(row[3], table_text_style)
        ])
        
    param_table = Table(table_data, colWidths=[150, 120, 150, 120])
    param_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1f3b68')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0,1), (-1,-1), 5),
        ('BOTTOMPADDING', (0,1), (-1,-1), 5),
    ]))
    
    story.append(param_table)
    story.append(Spacer(1, 30))
    
    # 5. Disclaimer/Signature
    disclaimer_style = ParagraphStyle(
        'DocDisclaimer',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        textColor=colors.HexColor('#94a3b8'),
        spaceBefore=20
    )
    story.append(Paragraph("Disclaimer: This report is generated by an AI-Powered Flood Prediction System based on machine learning classifications (XGBoost/RandomForest). Predictions are probabilistic and should be cross-referenced with national meteorological bulletins and local emergency advice.", disclaimer_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
