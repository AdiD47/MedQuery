"""
PDF Report Generator for Research Findings
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
import os
from pathlib import Path


def generate_research_report(research_data: dict, output_path: str) -> str:
    """
    Generate a professional PDF report from research data
    
    Args:
        research_data: Dictionary containing research findings
        output_path: Path where PDF should be saved
    
    Returns:
        Path to generated PDF file
    """
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a365d'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c5282'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#2d3748'),
        spaceAfter=6,
        spaceBefore=6,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        textColor=colors.HexColor('#2d3748'),
        spaceAfter=12,
        alignment=TA_JUSTIFY,
        fontName='Helvetica'
    )
    
    # Title Page
    elements.append(Spacer(1, 2*inch))
    elements.append(Paragraph("Pharmaceutical Research Intelligence Report", title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Query
    query_text = research_data.get('query', 'Research Query')
    elements.append(Paragraph(f"<b>Research Query:</b> {query_text}", body_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Date
    date_str = datetime.now().strftime("%B %d, %Y")
    elements.append(Paragraph(f"<b>Generated:</b> {date_str}", body_style))
    elements.append(PageBreak())
    
    # Executive Summary
    elements.append(Paragraph("Executive Summary", heading_style))
    elements.append(Spacer(1, 0.1*inch))
    
    exec_summary = research_data.get('executive_summary', 'Analysis of respiratory diseases in Indian market.')
    elements.append(Paragraph(exec_summary, body_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Key Findings
    elements.append(Paragraph("Key Findings", heading_style))
    findings = research_data.get('key_findings', [])
    
    for i, finding in enumerate(findings, 1):
        finding_text = f"{i}. {finding}"
        elements.append(Paragraph(finding_text, body_style))
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Disease Analysis Table
    elements.append(Paragraph("Disease Comparison", heading_style))
    elements.append(Spacer(1, 0.1*inch))
    
    diseases_data = research_data.get('diseases', [])
    
    if diseases_data:
        # Create table data
        table_data = [['Disease', 'Patient Burden', 'Competition', 'Market Size', 'Opportunity']]
        
        for disease in diseases_data:
            table_data.append([
                disease.get('name', 'N/A'),
                disease.get('burden', 'N/A'),
                disease.get('competition', 'N/A'),
                disease.get('market_size', 'N/A'),
                disease.get('opportunity', 'N/A')
            ])
        
        # Create table
        t = Table(table_data, colWidths=[1.5*inch, 1.3*inch, 1.2*inch, 1.2*inch, 1.3*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        elements.append(t)
        elements.append(Spacer(1, 0.3*inch))
    
    # Detailed Analysis
    elements.append(PageBreak())
    elements.append(Paragraph("Detailed Analysis", heading_style))
    elements.append(Spacer(1, 0.2*inch))
    
    for disease in diseases_data:
        disease_name = disease.get('name', 'Unknown Disease')
        elements.append(Paragraph(disease_name, subheading_style))
        
        # Clinical Trials
        if 'clinical_trials' in disease:
            elements.append(Paragraph(f"<b>Clinical Trials:</b> {disease['clinical_trials']}", body_style))
        
        # Market Data
        if 'market_data' in disease:
            elements.append(Paragraph(f"<b>Market Analysis:</b> {disease['market_data']}", body_style))
        
        # Patent Info
        if 'patent_info' in disease:
            elements.append(Paragraph(f"<b>Patent Landscape:</b> {disease['patent_info']}", body_style))
        
        elements.append(Spacer(1, 0.2*inch))
    
    # Recommendations
    elements.append(PageBreak())
    elements.append(Paragraph("Strategic Recommendations", heading_style))
    elements.append(Spacer(1, 0.1*inch))
    
    recommendations = research_data.get('recommendations', [])
    for i, rec in enumerate(recommendations, 1):
        rec_text = f"{i}. {rec}"
        elements.append(Paragraph(rec_text, body_style))
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Next Steps
    elements.append(Paragraph("Next Steps", heading_style))
    next_steps = research_data.get('next_steps', [])
    for i, step in enumerate(next_steps, 1):
        step_text = f"{i}. {step}"
        elements.append(Paragraph(step_text, body_style))
    
    # Build PDF
    doc.build(elements)
    
    return output_path


def create_sample_report():
    """Create a sample report for testing"""
    sample_data = {
        'query': 'Which respiratory diseases show low competition but high patient burden in India?',
        'executive_summary': 'Analysis of respiratory diseases in the Indian market reveals Interstitial Lung Disease (ILD) as a high-opportunity area with significant patient burden but relatively low competitive intensity.',
        'key_findings': [
            'ILD shows 850 Cr INR market size with 12.3% growth rate',
            'Only 2 major competitors (Roche, Boehringer) vs 4-5 in other respiratory segments',
            'Clinical trial activity 50% lower than COPD/Asthma',
            'Major patents expiring 2025-2026 creating generic opportunities',
            'High unmet medical need with limited treatment options'
        ],
        'diseases': [
            {
                'name': 'ILD',
                'burden': 'High',
                'competition': 'Low',
                'market_size': '850 Cr',
                'opportunity': 'High',
                'clinical_trials': '15 active trials in India, mostly Phase 2',
                'market_data': 'Market size 850 Cr INR, growing at 12.3%. Only 2 major players.',
                'patent_info': '25 patents expiring in next 2 years, high generic opportunity'
            },
            {
                'name': 'COPD',
                'burden': 'High',
                'competition': 'High',
                'market_size': '2500 Cr',
                'opportunity': 'Medium',
                'clinical_trials': '42 active trials in India, well-established R&D',
                'market_data': 'Market size 2500 Cr INR. 3 major competitors with 85% market share.',
                'patent_info': '32 patents expiring soon but intense competition expected'
            },
            {
                'name': 'Asthma',
                'burden': 'High',
                'competition': 'High',
                'market_size': '3200 Cr',
                'opportunity': 'Low',
                'clinical_trials': '58 active trials, highly competitive R&D landscape',
                'market_data': 'Market size 3200 Cr INR. 4 major players, saturated market.',
                'patent_info': 'Strong patent protection until 2028, low generic opportunity'
            }
        ],
        'recommendations': [
            'Prioritize ILD for immediate R&D investment due to high opportunity and lower competition',
            'Conduct detailed feasibility study for ILD drug development or acquisition',
            'Monitor patent expirations in ILD space for generic opportunities',
            'Consider partnerships with Roche or Boehringer for market entry'
        ],
        'next_steps': [
            'Commission detailed market research on ILD patient demographics',
            'Evaluate in-licensing opportunities for ILD compounds',
            'Assess manufacturing capabilities for ILD medications',
            'Initiate discussions with key opinion leaders in pulmonology'
        ]
    }
    
    output_path = "/app/backend/sample_report.pdf"
    return generate_research_report(sample_data, output_path)
