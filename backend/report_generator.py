from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_pdf_report(dataset, output_path):
    doc = SimpleDocTemplate(
        output_path, 
        pagesize=letter,
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=40
    )
    styles = getSampleStyleSheet()
    
    # Custom UNAR Brand Styles
    brand_dark = colors.HexColor('#0f172a')
    brand_teal = colors.HexColor('#10b981')
    brand_muted = colors.HexColor('#64748b')
    
    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Heading1'], fontSize=28, 
        spaceAfter=10, alignment=1, textColor=brand_dark, fontName='Helvetica-Bold'
    )
    tagline_style = ParagraphStyle(
        'Tagline', parent=styles['Normal'], alignment=1, 
        fontSize=12, spaceAfter=40, textColor=brand_teal, fontName='Helvetica-Oblique', letterSpacing=1
    )
    h2_style = ParagraphStyle(
        'Heading2', parent=styles['Heading2'], fontSize=16, 
        spaceBefore=20, spaceAfter=15, textColor=brand_dark, fontName='Helvetica-Bold'
    )
    h3_style = ParagraphStyle(
        'Heading3', parent=styles['Heading3'], fontSize=12, 
        spaceBefore=15, spaceAfter=8, textColor=brand_teal, fontName='Helvetica-Bold'
    )
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.black)
    bullet_style = ParagraphStyle('BulletStyle', parent=normal_style, leftIndent=15, firstLineIndent=-10)
    
    elements = []
    
    # --- HEADER ---
    elements.append(Paragraph("UNAR", title_style))
    elements.append(Paragraph("Know. Refine. Become.", tagline_style))
    
    # --- CANDIDATE INFO ---
    info_data = [
        ["Candidate Name:", dataset['candidate'].get('name', 'N/A')],
        ["Candidate ID:", dataset['candidate'].get('id', 'N/A')],
        ["Role/Department:", dataset['candidate'].get('department', 'N/A')],
        ["Interview Type:", dataset['candidate'].get('type', 'N/A')],
        ["Date:", dataset['interview'].get('endTime', dataset['interview'].get('startTime', ''))[:10]]
    ]
    
    t_info = Table(info_data, colWidths=[120, 400])
    t_info.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), brand_muted),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 30))
    
    final = dataset.get('finalAssessment', {})
    if not final:
        elements.append(Paragraph("Assessment incomplete or data unavailable.", normal_style))
        doc.build(elements)
        return
        
    # --- OVERALL PERFORMANCE ---
    elements.append(Paragraph("OVERALL PERFORMANCE", h2_style))
    
    score_data = [
        ["OVERALL SCORE", f"{final.get('overallScore', 0)} / 100"]
    ]
    
    for cat in final.get('categories', []):
        score_data.append([cat.get('name', 'Category'), f"{cat.get('score', 0)}%"])
    
    t_scores = Table(score_data, colWidths=[300, 100])
    t_scores.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), brand_dark),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(t_scores)
    elements.append(Spacer(1, 20))
    
    # --- STRENGTHS & IMPROVEMENTS ---
    elements.append(Paragraph("KEY PROFILE INSIGHTS", h2_style))
    
    elements.append(Paragraph("Top Strengths", h3_style))
    for s in final.get('topStrengths', []):
        elements.append(Paragraph(f"• {s}", bullet_style))
        
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Focus Areas", h3_style))
    for i in final.get('topImprovements', []):
        elements.append(Paragraph(f"• {i}", bullet_style))

    elements.append(PageBreak())
    
    # --- CAMERA & BODY LANGUAGE / VOICE ---
    elements.append(Paragraph("BEHAVIORAL & VOICE ANALYSIS", h2_style))
    
    # Calculate aggregates for the PDF
    q_count = len(dataset.get('questions', []))
    if q_count > 0:
        avgEye = sum(q.get('cameraMetrics', {}).get('eyeContact', 0) for q in dataset['questions']) / q_count
        avgHead = sum(q.get('cameraMetrics', {}).get('headStability', 0) for q in dataset['questions']) / q_count
        avgFace = sum(q.get('cameraMetrics', {}).get('facePresence', 0) for q in dataset['questions']) / q_count
        avgBlink = sum(q.get('cameraMetrics', {}).get('blinkRate', 0) for q in dataset['questions']) / q_count
        
        avgWpm = sum(q.get('voiceMetrics', {}).get('speechRate', 0) for q in dataset['questions']) / q_count
        avgPauses = sum(q.get('voiceMetrics', {}).get('longPauseCount', 0) for q in dataset['questions']) / q_count
        avgFillers = sum(q.get('voiceMetrics', {}).get('fillerWordCount', 0) for q in dataset['questions']) / q_count
    else:
        avgEye = avgHead = avgFace = avgBlink = avgWpm = avgPauses = avgFillers = 0

    behavior_data = [
        ["Camera & Body Language", "Metric"],
        ["Eye Contact", f"{round(avgEye)}%"],
        ["Head Stability", f"{round(avgHead)}%"],
        ["Face Presence", f"{round(avgFace)}%"],
        ["Average Blink Rate", f"{round(avgBlink)}/min"],
        ["", ""],
        ["Voice Analysis", "Metric"],
        ["Speech Rate (WPM)", f"{round(avgWpm)}"],
        ["Long Pauses (Avg per Q)", f"{round(avgPauses)}"],
        ["Filler Words (Avg per Q)", f"{round(avgFillers)}"],
    ]
    
    t_behav = Table(behavior_data, colWidths=[300, 100])
    t_behav.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), brand_dark),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
        ('BACKGROUND', (0, 6), (1, 6), brand_dark),
        ('TEXTCOLOR', (0, 6), (1, 6), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 6), (-1, 6), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(t_behav)
    elements.append(Spacer(1, 20))
    
    # --- QUESTION-WISE ANALYSIS ---
    elements.append(Paragraph("QUESTION-WISE ANALYSIS", h2_style))
    
    for q in dataset.get('questions', []):
        elements.append(Paragraph(f"Q{q.get('questionNumber')}: {q.get('question')}", h3_style))
        elements.append(Paragraph(f"<b>Score:</b> {q.get('answerScore', 0)} / 100", normal_style))
        elements.append(Spacer(1, 5))
        
        elements.append(Paragraph("<b>Your Response:</b>", normal_style))
        elements.append(Paragraph(q.get('transcript', 'No response recorded.'), normal_style))
        elements.append(Spacer(1, 5))
        
        if q.get('strengths'):
            elements.append(Paragraph("<b>Strengths:</b>", normal_style))
            for s in q.get('strengths', []):
                elements.append(Paragraph(f"• {s}", bullet_style))
                
        if q.get('improvements'):
            elements.append(Paragraph("<b>Improvements:</b>", normal_style))
            for i in q.get('improvements', []):
                elements.append(Paragraph(f"• {i}", bullet_style))
        
        elements.append(Spacer(1, 15))
        
    elements.append(PageBreak())
    
    # --- FINAL AI SUMMARY ---
    elements.append(Paragraph("FINAL AI SUMMARY", h2_style))
    elements.append(Paragraph(final.get('summary', 'No summary available.'), normal_style))
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("RECOMMENDED NEXT STEPS", h2_style))
    
    # Handle splitting bullet points from recommendation string if it exists
    rec_text = final.get('recommendation', 'No recommendations available.')
    # Simple split if it uses numbers like "1. "
    import re
    parts = re.split(r'\d+\.\s+', rec_text)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) > 1:
        for i, p in enumerate(parts):
            elements.append(Paragraph(f"{i+1}. {p}", bullet_style))
    else:
        elements.append(Paragraph(rec_text, normal_style))
        
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("UNAR • Know. Refine. Become.", ParagraphStyle('Footer', parent=styles['Normal'], alignment=1, textColor=brand_muted)))
    
    doc.build(elements)
