import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def safe_text(val):
    if isinstance(val, list):
        return ", ".join(str(v) for v in val)
    return str(val) if val is not None else ""


# PwC Brand Colors
ORANGE = RGBColor(208, 74, 2)       # #D04A02
CHARCOAL = RGBColor(45, 45, 45)     # #2D2D2D
GOLD = RGBColor(235, 163, 0)        # #EBA300
RED = RGBColor(163, 31, 52)         # #A31F34
OFF_WHITE = RGBColor(248, 249, 250) # #F8F9FA
WHITE = RGBColor(255, 255, 255)
GREY = RGBColor(180, 180, 180)
LIGHT_GREY = RGBColor(240, 240, 240)

def set_font(run, name="Arial", size=14, bold=False, color=CHARCOAL):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color

def create_slide_header(slide, title_text, subtitle_text=None):
    # Add a top header bar block
    header_box = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(10), Inches(0.9)
    )
    header_box.fill.solid()
    header_box.fill.fore_color.rgb = CHARCOAL
    header_box.line.color.rgb = ORANGE
    header_box.line.width = Pt(1.5)

    # Add title text
    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.1), Inches(9), Inches(0.7))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title_text
    p.alignment = PP_ALIGN.LEFT
    run = p.runs[0]
    set_font(run, size=24, bold=True, color=WHITE)

    # Add subtitle
    if subtitle_text:
        p2 = tf.add_paragraph()
        p2.text = subtitle_text
        run2 = p2.runs[0]
        set_font(run2, size=11, color=GOLD)

def add_footer(slide):
    # Footnote bar
    footer_box = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(7.1), Inches(10), Inches(0.4)
    )
    footer_box.fill.solid()
    footer_box.fill.fore_color.rgb = LIGHT_GREY
    footer_box.line.fill.background()

    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(7.1), Inches(9), Inches(0.3))
    p = txBox.text_frame.paragraphs[0]
    p.text = "PwC Solution Advisory  |  Autonomous Bid Lifecycle Platform  |  AI Draft - For Internal Review Only"
    p.alignment = PP_ALIGN.LEFT
    set_font(p.runs[0], size=8, bold=False, color=CHARCOAL)

def generate_pptx(data, output_path):
    prs = Presentation()
    # Standard 4:3 is default, let's change to 16:9 widescreen
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)
    
    # ----------------------------------------------------
    # SLIDE 1: Title Cover (Dark/Orange Premium Design)
    # ----------------------------------------------------
    blank_slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_slide_layout)
    
    # Set background color
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(10), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = CHARCOAL
    bg.line.fill.background()

    # Brand Accent Bar
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.3), Inches(7.5))
    bar.fill.solid()
    bar.fill.fore_color.rgb = ORANGE
    bar.line.fill.background()

    # Title box
    title_box = slide.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(8), Inches(3.0))
    tf = title_box.text_frame
    tf.word_wrap = True
    
    p_pre = tf.paragraphs[0]
    p_pre.text = "PWC IT SOLUTION PROPOSAL"
    set_font(p_pre.runs[0], size=14, bold=True, color=GOLD)
    
    p_main = tf.add_paragraph()
    p_main.text = safe_text(data.get("proposal_title", "Autonomous Solution Design"))
    set_font(p_main.runs[0], size=36, bold=True, color=WHITE)
    
    p_sub = tf.add_paragraph()
    p_sub.text = f"Prepared for: {safe_text(data.get('client_name', 'Enterprise Client'))}"
    set_font(p_sub.runs[0], size=18, color=LIGHT_GREY)
    
    p_meta = tf.add_paragraph()
    p_meta.text = f"\nTimeline: {safe_text(data.get('project_duration', 'N/A'))}  |  Target Budget: {safe_text(data.get('budget', 'N/A'))}\nDraft Date: July 2026"
    set_font(p_meta.runs[0], size=11, color=ORANGE)

    # ----------------------------------------------------
    # SLIDE 1A: Business Summary
    # ----------------------------------------------------
    slide = prs.slides.add_slide(blank_slide_layout)
    create_slide_header(slide, "Business Summary", "Executive overview of the proposed solution")
    add_footer(slide)

    summary_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(9.0), Inches(5.0))
    tf_sum = summary_box.text_frame
    tf_sum.word_wrap = True
    
    business_summary = data.get("business_summary", "No business summary provided.")
    for paragraph in business_summary.split('\n'):
        if paragraph.strip():
            p_sum = tf_sum.add_paragraph()
            p_sum.text = safe_text(paragraph.strip())
            set_font(p_sum.runs[0], size=14, color=CHARCOAL)
            p_sum.space_after = Pt(14)

    # ----------------------------------------------------
    # SLIDE 2: Client Requirements & Gap Analysis
    # ----------------------------------------------------
    slide = prs.slides.add_slide(blank_slide_layout)
    create_slide_header(slide, "Client Requirements & Gap Analysis", "RAG-driven competence matching against RFP requirements")
    add_footer(slide)

    # Requirements list (Left panel)
    req_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(1.3), Inches(4.3), Inches(5.5))
    req_box.fill.solid()
    req_box.fill.fore_color.rgb = OFF_WHITE
    req_box.line.color.rgb = CHARCOAL
    req_box.line.width = Pt(1)
    
    req_title = slide.shapes.add_textbox(Inches(0.6), Inches(1.4), Inches(4.1), Inches(5.2))
    tf_req = req_title.text_frame
    tf_req.word_wrap = True
    p = tf_req.paragraphs[0]
    p.text = "Key Client Requirements:"
    set_font(p.runs[0], size=14, bold=True, color=ORANGE)
    
    for req in data.get("requirements", ["No requirements specified"]):
        p_item = tf_req.add_paragraph()
        p_item.text = f"• {safe_text(req)}"
        set_font(p_item.runs[0], size=11, color=CHARCOAL)

    # Gaps and Matches (Right panel)
    gap_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(5.2), Inches(1.3), Inches(4.3), Inches(5.5))
    gap_box.fill.solid()
    gap_box.fill.fore_color.rgb = OFF_WHITE
    gap_box.line.color.rgb = CHARCOAL
    gap_box.line.width = Pt(1)

    gap_title = slide.shapes.add_textbox(Inches(5.3), Inches(1.4), Inches(4.1), Inches(5.2))
    tf_gap = gap_title.text_frame
    tf_gap.word_wrap = True
    p_gap = tf_gap.paragraphs[0]
    p_gap.text = "Capability Gaps & Mitigations:"
    set_font(p_gap.runs[0], size=14, bold=True, color=RED)

    for gap in data.get("gaps", ["No gaps identified"]):
        p_item = tf_gap.add_paragraph()
        p_item.text = f"• {safe_text(gap)}"
        set_font(p_item.runs[0], size=11, color=CHARCOAL)

    # ----------------------------------------------------
    # SLIDE 3: Solution Approach & Architecture
    # ----------------------------------------------------
    slide = prs.slides.add_slide(blank_slide_layout)
    create_slide_header(slide, "Solution Approach & Architecture", "High-level implementation strategy and operational frameworks")
    add_footer(slide)

    # 3-Pillar Solution display
    pillars = data.get("solution_pillars", [
        {"title": "Pillar 1", "desc": "Description 1"},
        {"title": "Pillar 2", "desc": "Description 2"},
        {"title": "Pillar 3", "desc": "Description 3"}
    ])

    width_pillar = Inches(2.7)
    gap_pillar = Inches(0.4)
    start_left = Inches(0.5)

    for i, pillar in enumerate(pillars[:3]):
        left = start_left + i * (width_pillar + gap_pillar)
        
        # Pillar Shape
        p_shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, Inches(1.8), width_pillar, Inches(4.5))
        p_shape.fill.solid()
        p_shape.fill.fore_color.rgb = OFF_WHITE
        p_shape.line.color.rgb = ORANGE
        p_shape.line.width = Pt(2)
        
        # Pillar Number Box
        n_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, Inches(1.8), width_pillar, Inches(0.6))
        n_shape.fill.solid()
        n_shape.fill.fore_color.rgb = ORANGE
        n_shape.line.fill.background()
        
        # Pillar text inside number box
        p_num = n_shape.text_frame.paragraphs[0]
        p_num.text = f"0{i+1}. {safe_text(pillar.get('title'))}"
        p_num.alignment = PP_ALIGN.CENTER
        set_font(p_num.runs[0], size=12, bold=True, color=WHITE)
        
        # Pillar Description text box
        desc_box = slide.shapes.add_textbox(left + Inches(0.1), Inches(2.5), width_pillar - Inches(0.2), Inches(3.6))
        tf_desc = desc_box.text_frame
        tf_desc.word_wrap = True
        p_desc = tf_desc.paragraphs[0]
        p_desc.text = safe_text(pillar.get("desc", ""))
        set_font(p_desc.runs[0], size=11, color=CHARCOAL)

    # ----------------------------------------------------
    # SLIDE 3B: High Level Design: Data Flow
    # ----------------------------------------------------
    slide = prs.slides.add_slide(blank_slide_layout)
    create_slide_header(slide, "High Level Design: Data Flow", "Data processing pipeline and integration points")
    add_footer(slide)

    data_flow = data.get("data_flow", [])
    
    if data_flow:
        df_width = Inches(8.0 / len(data_flow))
        for i, step in enumerate(data_flow):
            left = Inches(1.0) + (i * df_width)
            
            # Step Box
            s_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, Inches(2.5), df_width - Inches(0.2), Inches(2.0))
            s_box.fill.solid()
            s_box.fill.fore_color.rgb = OFF_WHITE
            s_box.line.color.rgb = ORANGE
            s_box.line.width = Pt(1.5)
            
            tf_s = s_box.text_frame
            tf_s.word_wrap = True
            p_s = tf_s.paragraphs[0]
            p_s.text = safe_text(step)
            p_s.alignment = PP_ALIGN.CENTER
            set_font(p_s.runs[0], size=11, bold=True, color=CHARCOAL)
            
            # Arrow
            if i < len(data_flow) - 1:
                arrow = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, left + df_width - Inches(0.15), Inches(3.3), Inches(0.2), Inches(0.4))
                arrow.fill.solid()
                arrow.fill.fore_color.rgb = GOLD
                arrow.line.fill.background()

    # ----------------------------------------------------
    # SLIDE 4: Landscape Architecture
    # ----------------------------------------------------
    slide = prs.slides.add_slide(blank_slide_layout)
    create_slide_header(slide, "Landscape & Architecture", "Reference systems architecture and integration patterns")
    add_footer(slide)

    arch_layers = data.get("architecture", [
        {"name": "Client Access / Presentation Layer", "components": ["Web Portal", "Mobile Client", "API Gateway"]},
        {"name": "Application Logic & Agents Core", "components": ["Orchestrator Engine", "Estimation Engine", "Document Agent"]},
        {"name": "Data Integration & Knowledge", "components": ["MySQL Database", "Qdrant Vector DB", "Asset Library"]}
    ])

    for i, layer in enumerate(arch_layers[:4]):
        top = Inches(1.5 + (i * 1.3))
        
        # Layer Container
        layer_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), top, Inches(9.0), Inches(1.0))
        layer_box.fill.solid()
        layer_box.fill.fore_color.rgb = OFF_WHITE
        layer_box.line.color.rgb = GOLD
        layer_box.line.width = Pt(1.5)
        
        # Layer Header Box (left side)
        hdr_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), top, Inches(2.5), Inches(1.0))
        hdr_box.fill.solid()
        hdr_box.fill.fore_color.rgb = CHARCOAL
        hdr_box.line.fill.background()
        
        p_hdr = hdr_box.text_frame.paragraphs[0]
        p_hdr.text = safe_text(layer.get("name", ""))
        p_hdr.alignment = PP_ALIGN.CENTER
        set_font(p_hdr.runs[0], size=11, bold=True, color=WHITE)
        
        # Component boxes inside the layer
        comps = layer.get("components", [])
        if comps:
            c_width = Inches(6.0 / len(comps))
            for j, comp in enumerate(comps):
                c_left = Inches(3.2) + (j * c_width)
                c_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left, top + Inches(0.15), c_width - Inches(0.15), Inches(0.7))
                c_box.fill.solid()
                c_box.fill.fore_color.rgb = WHITE
                c_box.line.color.rgb = ORANGE
                c_box.line.width = Pt(1)
                
                p_comp = c_box.text_frame.paragraphs[0]
                p_comp.text = safe_text(comp)
                p_comp.alignment = PP_ALIGN.CENTER
                set_font(p_comp.runs[0], size=10, bold=True, color=CHARCOAL)

    # ----------------------------------------------------
    # SLIDE 4B: Infrastructure Approximation
    # ----------------------------------------------------
    slide = prs.slides.add_slide(blank_slide_layout)
    create_slide_header(slide, "Infrastructure Approximation", "Estimated cloud infrastructure components and costs")
    add_footer(slide)

    infra_items = data.get("infrastructure_approximation", [])
    
    if infra_items:
        infra_rows = len(infra_items) + 1
        infra_cols = 3
        infra_table_shape = slide.shapes.add_table(infra_rows, infra_cols, Inches(1.0), Inches(2.0), Inches(8.0), Inches(0.5 * infra_rows))
        i_table = infra_table_shape.table
        
        i_table.columns[0].width = Inches(2.5)
        i_table.columns[1].width = Inches(3.5)
        i_table.columns[2].width = Inches(2.0)
        
        i_headers = ["Component", "Specification", "Est. Monthly Cost"]
        for j, hdr in enumerate(i_headers):
            cell = i_table.cell(0, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = CHARCOAL
            p = cell.text_frame.paragraphs[0]
            p.text = hdr
            p.alignment = PP_ALIGN.CENTER
            set_font(p.runs[0], size=12, bold=True, color=WHITE)
            
        for i, item in enumerate(infra_items):
            row_idx = i + 1
            vals = [item.get("component"), item.get("spec"), str(item.get("estimated_monthly_cost"))]
            for j, val in enumerate(vals):
                cell = i_table.cell(row_idx, j)
                cell.fill.solid()
                cell.fill.fore_color.rgb = WHITE if row_idx % 2 == 0 else OFF_WHITE
                p = cell.text_frame.paragraphs[0]
                p.text = safe_text(val)
                p.alignment = PP_ALIGN.CENTER if j == 2 else PP_ALIGN.LEFT
                set_font(p.runs[0], size=11, color=CHARCOAL)

    # ----------------------------------------------------
    # SLIDE 5: Project Timeline
    # ----------------------------------------------------
    slide = prs.slides.add_slide(blank_slide_layout)
    create_slide_header(slide, "Project Timeline", "Sequential delivery phases and target deliverables")
    add_footer(slide)

    phases = data.get("timeline_phases", [
        {"phase": "Phase 1: Inception & Discovery", "duration": "Weeks 1-4", "deliverables": "Parsed specifications, initial architectural blueprint"},
        {"phase": "Phase 2: Core Engineering & RAG Setup", "duration": "Weeks 5-12", "deliverables": "Database sync, orchestration engines integration"},
        {"phase": "Phase 3: UAT & Client Handover", "duration": "Weeks 13-16", "deliverables": "Production deployment, final document sign-off"}
    ])

    for i, phase in enumerate(phases[:3]):
        top = Inches(1.5 + (i * 1.7))
        
        # Chevron Phase Box
        c_shape = slide.shapes.add_shape(MSO_SHAPE.CHEVRON, Inches(0.5), top, Inches(3.2), Inches(1.3))
        c_shape.fill.solid()
        c_shape.fill.fore_color.rgb = ORANGE
        c_shape.line.fill.background()
        
        # Chevron Text
        tf_c = c_shape.text_frame
        tf_c.word_wrap = True
        p_c = tf_c.paragraphs[0]
        p_c.text = safe_text(phase.get("phase", ""))
        p_c.alignment = PP_ALIGN.CENTER
        set_font(p_c.runs[0], size=11, bold=True, color=WHITE)
        
        p_dur = tf_c.add_paragraph()
        p_dur.text = f"({safe_text(phase.get('duration', ''))})"
        p_dur.alignment = PP_ALIGN.CENTER
        set_font(p_dur.runs[0], size=10, color=GOLD)

        # Description / Deliverables Box next to the Chevron
        d_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(4.0), top, Inches(5.5), Inches(1.3))
        d_box.fill.solid()
        d_box.fill.fore_color.rgb = OFF_WHITE
        d_box.line.color.rgb = CHARCOAL
        d_box.line.width = Pt(1)
        
        tf_d = d_box.text_frame
        tf_d.word_wrap = True
        p_d = tf_d.paragraphs[0]
        p_d.text = "Key Deliverables / Activities:"
        set_font(p_d.runs[0], size=11, bold=True, color=CHARCOAL)
        
        p_d_desc = tf_d.add_paragraph()
        p_d_desc.text = safe_text(phase.get("deliverables", ""))
        set_font(p_d_desc.runs[0], size=10, color=CHARCOAL)

    # ----------------------------------------------------
    # SLIDE 5B: Similar Projects
    # ----------------------------------------------------
    slide = prs.slides.add_slide(blank_slide_layout)
    create_slide_header(slide, "Similar Projects", "Past credentials and successful delivery outcomes")
    add_footer(slide)

    sim_projects = data.get("similar_projects", [])
    
    if sim_projects:
        for i, proj in enumerate(sim_projects[:2]):
            top = Inches(2.0 + (i * 2.2))
            
            p_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), top, Inches(8.0), Inches(1.8))
            p_box.fill.solid()
            p_box.fill.fore_color.rgb = OFF_WHITE
            p_box.line.color.rgb = GOLD
            p_box.line.width = Pt(1.5)
            
            tf_p = p_box.text_frame
            tf_p.word_wrap = True
            
            p_title = tf_p.paragraphs[0]
            p_title.text = f"{safe_text(proj.get('client_industry', 'Industry'))} | {safe_text(proj.get('project_name', 'Project'))}"
            set_font(p_title.runs[0], size=14, bold=True, color=ORANGE)
            
            p_outcome = tf_p.add_paragraph()
            p_outcome.text = f"Outcome: {safe_text(proj.get('outcome', ''))}"
            set_font(p_outcome.runs[0], size=12, color=CHARCOAL)

    # ----------------------------------------------------
    # SLIDE 6: Effort & Person-Hour Conversion
    # ----------------------------------------------------
    slide = prs.slides.add_slide(blank_slide_layout)
    create_slide_header(slide, "Effort & Person-Hour Conversion", "Allocated program FTE structure, rate cards, and financial sizing")
    add_footer(slide)

    # Table layout
    resources = data.get("resources", [
        {"role": "Engagement Partner", "loc": "Onsite", "fte": "0.25", "rate": "$30,000", "total": "$45,000", "person_days": 10},
        {"role": "Lead Architect", "loc": "Onsite / Hybrid", "fte": "1.00", "rate": "$24,000", "total": "$144,000", "person_days": 60},
        {"role": "Senior Frontend Developer", "loc": "Offshore", "fte": "2.00", "rate": "$8,000", "total": "$96,000", "person_days": 120},
        {"role": "Senior Backend Developer", "loc": "Offshore", "fte": "2.00", "rate": "$8,000", "total": "$96,000", "person_days": 120},
        {"role": "DevOps & Security Specialist", "loc": "Offshore", "fte": "1.00", "rate": "$9,000", "total": "$54,000", "person_days": 60}
    ])
    
    rows = len(resources) + 1
    # Cap rows to fit on one slide
    rows = min(rows, 9)
    cols = 6
    
    # Calculate a sensible height for the table depending on rows
    table_height = Inches(0.4 * rows)
    table_shape = slide.shapes.add_table(rows, cols, Inches(0.5), Inches(1.5), Inches(9.0), table_height)
    table = table_shape.table

    # Column Widths
    table.columns[0].width = Inches(2.0) # Role
    table.columns[1].width = Inches(1.2) # Location
    table.columns[2].width = Inches(1.2) # Count (FTE)
    table.columns[3].width = Inches(1.5) # Monthly Rate
    table.columns[4].width = Inches(1.3) # Person Days
    table.columns[5].width = Inches(1.8) # Total Sizing

    headers = ["Role / Competency", "Delivery Location", "FTE Count", "Monthly Rate", "Person Days", "Total Financial Sizing"]
    for j, header in enumerate(headers):
        cell = table.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = CHARCOAL
        p = cell.text_frame.paragraphs[0]
        p.text = safe_text(header)
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], size=11, bold=True, color=WHITE)

    for i, res in enumerate(resources[:rows-1]):
        row_idx = i + 1
        cols_val = [res.get("role"), res.get("loc"), res.get("fte"), res.get("rate"), str(res.get("person_days", "N/A")), res.get("total")]
        for j, val in enumerate(cols_val):
            cell = table.cell(row_idx, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if row_idx % 2 == 0 else OFF_WHITE
            p = cell.text_frame.paragraphs[0]
            p.text = safe_text(val)
            p.alignment = PP_ALIGN.CENTER if j > 0 else PP_ALIGN.LEFT
            set_font(p.runs[0], size=10, bold=(j == 0), color=CHARCOAL)

    # ----------------------------------------------------
    # SLIDE 7: Required Skills & PwC Competency Matching
    # ----------------------------------------------------
    slide = prs.slides.add_slide(blank_slide_layout)
    create_slide_header(slide, "Skills Inventory & PwC Competency Mapping", "Required technical capabilities grounded in organizational assets")
    add_footer(slide)

    skills_map = data.get("skills_mapping", [
        {"skill": "React 18, TypeScript, Tailwind", "role": "Frontend Developer", "asset": "PwC Frontend Competency Center", "conf": "High (95%)"},
        {"skill": "Flask API, Python Core", "role": "Backend Developer", "asset": "PwC Python/Data Competency Team", "conf": "High (90%)"},
        {"skill": "MySQL Connector, RAG Store", "role": "Database Architect", "asset": "Enterprise Data Governance Framework", "conf": "Medium (85%)"},
        {"skill": "python-pptx Engine", "role": "Orchestrator Agent", "asset": "PwC Proposal Creator Accelerator Asset", "conf": "High (95%)"},
        {"skill": "CI/CD & DevOps", "role": "DevOps Engineer", "asset": "PwC DevOps Pipeline Accelerator", "conf": "High (98%)"}
    ])
    
    rows2 = len(skills_map) + 1
    # Cap rows to fit on one slide
    rows2 = min(rows2, 9)
    cols2 = 4
    
    table_height2 = Inches(0.4 * rows2)
    table_shape2 = slide.shapes.add_table(rows2, cols2, Inches(0.5), Inches(1.5), Inches(9.0), table_height2)
    table2 = table_shape2.table

    table2.columns[0].width = Inches(2.2) # Skill Name
    table2.columns[1].width = Inches(2.0) # Target Role
    table2.columns[2].width = Inches(3.5) # Associated PwC Asset/Team
    table2.columns[3].width = Inches(1.3) # Fit Confidence

    headers2 = ["Technical Skill", "Target Project Role", "Associated PwC Asset / Capability Team", "Fit Confidence"]
    for j, header in enumerate(headers2):
        cell = table2.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = ORANGE
        p = cell.text_frame.paragraphs[0]
        p.text = safe_text(header)
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], size=11, bold=True, color=WHITE)

    for i, item in enumerate(skills_map[:rows2-1]):
        row_idx = i + 1
        cols_val = [item.get("skill"), item.get("role"), item.get("asset"), item.get("conf")]
        for j, val in enumerate(cols_val):
            cell = table2.cell(row_idx, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if row_idx % 2 == 0 else OFF_WHITE
            p = cell.text_frame.paragraphs[0]
            p.text = safe_text(val)
            p.alignment = PP_ALIGN.CENTER if j == 3 else PP_ALIGN.LEFT
            set_font(p.runs[0], size=10, bold=(j == 0), color=CHARCOAL)

    # Save presentation
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    prs.save(output_path)
    print(f"Presentation saved successfully at: {output_path}")
