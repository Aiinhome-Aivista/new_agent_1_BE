import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def safe_text(val):
    if isinstance(val, list):
        return ", ".join(str(v) for v in val)
    return str(val) if val is not None else ""


# Brand Colors
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
    p.text = "Solution Advisory  |  Autonomous Bid Lifecycle Platform  |  AI Draft - For Internal Review Only"
    p.alignment = PP_ALIGN.LEFT
    set_font(p.runs[0], size=8, bold=False, color=CHARCOAL)


def add_reference_architecture_slide(slide, prs):
    # Background
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(10), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = WHITE
    bg.line.fill.background()

    create_slide_header(slide, "Reference Architecture", "Enterprise logical data patterns")
    add_footer(slide)

    # Cloud Box (Light Green)
    cloud_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(2.2), Inches(1.3), Inches(4.5), Inches(3.4))
    cloud_box.fill.solid()
    cloud_box.fill.fore_color.rgb = RGBColor(238, 247, 233)
    cloud_box.line.color.rgb = RGBColor(200, 220, 190)
    p = cloud_box.text_frame.paragraphs[0]
    p.text = "CLOUD"
    p.alignment = PP_ALIGN.LEFT
    set_font(p.runs[0], size=8, bold=True)
    
    # ON-PREM Box (Light Grey)
    onprem_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(2.2), Inches(4.8), Inches(4.5), Inches(2.0))
    onprem_box.fill.solid()
    onprem_box.fill.fore_color.rgb = RGBColor(245, 245, 245)
    onprem_box.line.color.rgb = GREY
    p = onprem_box.text_frame.paragraphs[0]
    p.text = "ON-PREM (Optional)"
    p.alignment = PP_ALIGN.LEFT
    set_font(p.runs[0], size=8, bold=True)
    
    # External Data Sources
    tx = slide.shapes.add_textbox(Inches(0.2), Inches(1.3), Inches(1.5), Inches(0.4))
    p = tx.text_frame.paragraphs[0]
    p.text = "External Data\nSources"
    p.alignment = PP_ALIGN.CENTER
    set_font(p.runs[0], size=10, bold=True)
    
    # Internal Data Sources
    tx2 = slide.shapes.add_textbox(Inches(0.2), Inches(4.8), Inches(1.5), Inches(0.4))
    p2 = tx2.text_frame.paragraphs[0]
    p2.text = "Internal Data\nSources"
    p2.alignment = PP_ALIGN.CENTER
    set_font(p2.runs[0], size=10, bold=True)

    # Some Data source DBs
    ds1 = slide.shapes.add_shape(MSO_SHAPE.CAN, Inches(0.6), Inches(2.0), Inches(0.7), Inches(0.8))
    ds1.fill.solid()
    ds1.fill.fore_color.rgb = WHITE
    ds1.line.color.rgb = CHARCOAL
    
    # Raw Data Zone
    raw_zone = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(2.5), Inches(1.6), Inches(1.3), Inches(1.7))
    raw_zone.fill.solid()
    raw_zone.fill.fore_color.rgb = WHITE
    raw_zone.line.color.rgb = GREY
    
    tx_raw = slide.shapes.add_textbox(Inches(2.5), Inches(1.6), Inches(1.3), Inches(0.3))
    p = tx_raw.text_frame.paragraphs[0]
    p.text = "RAW DATA ZONE"
    p.alignment = PP_ALIGN.CENTER
    set_font(p.runs[0], size=8, bold=True)
    
    tx_raw_os = slide.shapes.add_textbox(Inches(2.5), Inches(2.9), Inches(1.3), Inches(0.3))
    p = tx_raw_os.text_frame.paragraphs[0]
    p.text = "Object Storage"
    p.alignment = PP_ALIGN.CENTER
    set_font(p.runs[0], size=8, bold=False)

    # Database in Raw Data Zone
    raw_db = slide.shapes.add_shape(MSO_SHAPE.CAN, Inches(2.8), Inches(2.0), Inches(0.7), Inches(0.8))
    raw_db.fill.solid()
    raw_db.fill.fore_color.rgb = WHITE
    raw_db.line.color.rgb = ORANGE
    p = raw_db.text_frame.paragraphs[0]
    p.text = "Raw DB"
    p.alignment = PP_ALIGN.CENTER
    set_font(p.runs[0], size=7, bold=True)

    # Curated Zone
    cur_zone = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(4.0), Inches(1.6), Inches(1.3), Inches(1.7))
    cur_zone.fill.solid()
    cur_zone.fill.fore_color.rgb = WHITE
    cur_zone.line.color.rgb = GREY
    
    tx_cur = slide.shapes.add_textbox(Inches(4.0), Inches(1.6), Inches(1.3), Inches(0.3))
    p = tx_cur.text_frame.paragraphs[0]
    p.text = "CURATED ZONE"
    p.alignment = PP_ALIGN.CENTER
    set_font(p.runs[0], size=8, bold=True)
    
    tx_cur_os = slide.shapes.add_textbox(Inches(4.0), Inches(2.9), Inches(1.3), Inches(0.3))
    p = tx_cur_os.text_frame.paragraphs[0]
    p.text = "Object Storage"
    p.alignment = PP_ALIGN.CENTER
    set_font(p.runs[0], size=8, bold=False)

    cur_db = slide.shapes.add_shape(MSO_SHAPE.CAN, Inches(4.3), Inches(2.0), Inches(0.7), Inches(0.8))
    cur_db.fill.solid()
    cur_db.fill.fore_color.rgb = WHITE
    cur_db.line.color.rgb = ORANGE
    p = cur_db.text_frame.paragraphs[0]
    p.text = "Curated DB"
    p.alignment = PP_ALIGN.CENTER
    set_font(p.runs[0], size=7, bold=True)

    # Datamarts
    dm_zone = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(5.6), Inches(1.6), Inches(0.9), Inches(2.9))
    dm_zone.fill.solid()
    dm_zone.fill.fore_color.rgb = RGBColor(250, 250, 250)
    dm_zone.line.color.rgb = GREY
    
    tx_dm = slide.shapes.add_textbox(Inches(5.6), Inches(1.6), Inches(0.9), Inches(0.3))
    p = tx_dm.text_frame.paragraphs[0]
    p.text = "DATAMARTS"
    p.alignment = PP_ALIGN.CENTER
    set_font(p.runs[0], size=8, bold=True)
    
    dm1 = slide.shapes.add_shape(MSO_SHAPE.CAN, Inches(5.8), Inches(2.0), Inches(0.5), Inches(0.6))
    dm1.fill.solid(); dm1.fill.fore_color.rgb = WHITE; dm1.line.color.rgb = CHARCOAL
    dm2 = slide.shapes.add_shape(MSO_SHAPE.CAN, Inches(5.8), Inches(2.8), Inches(0.5), Inches(0.6))
    dm2.fill.solid(); dm2.fill.fore_color.rgb = WHITE; dm2.line.color.rgb = CHARCOAL
    dm3 = slide.shapes.add_shape(MSO_SHAPE.CAN, Inches(5.8), Inches(3.6), Inches(0.5), Inches(0.6))
    dm3.fill.solid(); dm3.fill.fore_color.rgb = WHITE; dm3.line.color.rgb = CHARCOAL

    # Data flow lines (Arrows)
    slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(1.4), Inches(2.4), Inches(1.0), Inches(0.15))
    slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(1.4), Inches(5.0), Inches(1.0), Inches(0.15))
    slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(3.8), Inches(2.4), Inches(0.2), Inches(0.15))
    slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(5.3), Inches(2.4), Inches(0.3), Inches(0.15))
    slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(6.5), Inches(2.4), Inches(0.5), Inches(0.15))

    # Use Cases
    tx3 = slide.shapes.add_textbox(Inches(7.3), Inches(1.3), Inches(2.0), Inches(0.4))
    p3 = tx3.text_frame.paragraphs[0]
    p3.text = "Use Cases"
    p3.alignment = PP_ALIGN.CENTER
    set_font(p3.runs[0], size=10, bold=True)

    use_cases = ["Cloud API", "Data & service exchange", "Advanced Analytics", "IoT Apps", "Business Intelligence", "3rd Party Apps"]
    for i, uc in enumerate(use_cases):
        r = i // 2
        c = i % 2
        uc_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(7.0 + c*1.3), Inches(1.8 + r*0.8), Inches(1.2), Inches(0.6))
        uc_box.fill.solid()
        uc_box.fill.fore_color.rgb = RGBColor(245, 250, 245)
        uc_box.line.color.rgb = GREY
        p = uc_box.text_frame.paragraphs[0]
        p.text = uc
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], size=8)


def add_azure_landscape_architecture_slide(slide, prs):
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(10), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = WHITE
    bg.line.fill.background()

    create_slide_header(slide, "Landscape Architecture (Azure Cloud Platform)", "Azure Native Services & Integration Topology")
    add_footer(slide)
    
    azure_blue = RGBColor(0, 114, 198)

    # Left: SAP HANA, SAP Ariba, Digital Apps
    sap1 = slide.shapes.add_shape(MSO_SHAPE.CAN, Inches(0.5), Inches(1.8), Inches(1.0), Inches(1.0))
    sap1.fill.solid()
    sap1.fill.fore_color.rgb = WHITE
    sap1.line.color.rgb = azure_blue
    p = sap1.text_frame.paragraphs[0]
    p.text = "SAP HANA"
    p.alignment = PP_ALIGN.CENTER
    set_font(p.runs[0], size=9, bold=True)
    
    sap2 = slide.shapes.add_shape(MSO_SHAPE.CAN, Inches(0.5), Inches(3.2), Inches(1.0), Inches(1.0))
    sap2.fill.solid()
    sap2.fill.fore_color.rgb = WHITE
    sap2.line.color.rgb = azure_blue
    p = sap2.text_frame.paragraphs[0]
    p.text = "SAP Ariba"
    p.alignment = PP_ALIGN.CENTER
    set_font(p.runs[0], size=9, bold=True)

    app1 = slide.shapes.add_shape(MSO_SHAPE.CAN, Inches(0.5), Inches(4.6), Inches(1.0), Inches(1.0))
    app1.fill.solid()
    app1.fill.fore_color.rgb = WHITE
    app1.line.color.rgb = azure_blue
    p = app1.text_frame.paragraphs[0]
    p.text = "Digital Apps"
    p.alignment = PP_ALIGN.CENTER
    set_font(p.runs[0], size=9, bold=True)

    # Middle: ELT / Orchestration Tool (Azure Data Factory)
    adf_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(2.3), Inches(1.5), Inches(2.2), Inches(2.8))
    adf_box.fill.solid()
    adf_box.fill.fore_color.rgb = WHITE
    adf_box.line.color.rgb = azure_blue
    try:
        adf_box.line.dash_style = 2
    except:
        pass
        
    tx_adf = slide.shapes.add_textbox(Inches(2.3), Inches(3.7), Inches(2.2), Inches(0.4))
    p = tx_adf.text_frame.paragraphs[0]
    p.text = "ELT/Orchestration Tool"
    p.alignment = PP_ALIGN.CENTER
    set_font(p.runs[0], size=10, bold=True)

    adf_icon = slide.shapes.add_shape(MSO_SHAPE.CLOUD, Inches(2.8), Inches(1.8), Inches(1.2), Inches(0.9))
    adf_icon.fill.solid()
    adf_icon.fill.fore_color.rgb = azure_blue
    p = adf_icon.text_frame.paragraphs[0]
    p.text = "ADF"
    p.alignment = PP_ALIGN.CENTER
    set_font(p.runs[0], size=10, color=WHITE, bold=True)

    # Azure SQL Server
    sql_box = slide.shapes.add_shape(MSO_SHAPE.CAN, Inches(5.2), Inches(1.2), Inches(1.2), Inches(1.2))
    sql_box.fill.solid()
    sql_box.fill.fore_color.rgb = WHITE
    sql_box.line.color.rgb = azure_blue
    
    tx_sql = slide.shapes.add_textbox(Inches(5.2), Inches(1.5), Inches(1.2), Inches(0.6))
    p = tx_sql.text_frame.paragraphs[0]
    p.text = "SQL Server"
    p.alignment = PP_ALIGN.CENTER
    set_font(p.runs[0], size=9, bold=True)
    
    # Pyramid / Triangle for Azure Synapse
    syn_box = slide.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE, Inches(6.8), Inches(2.2), Inches(2.5), Inches(3.5))
    syn_box.fill.solid()
    syn_box.fill.fore_color.rgb = RGBColor(220, 235, 250)
    syn_box.line.color.rgb = azure_blue
    
    tx_syn = slide.shapes.add_textbox(Inches(6.8), Inches(3.2), Inches(2.5), Inches(1.5))
    p = tx_syn.text_frame.paragraphs[0]
    p.text = "Reporting Layer\n\nCommon Data\n\nRAW Layer"
    p.alignment = PP_ALIGN.CENTER
    set_font(p.runs[0], size=9, bold=True, color=CHARCOAL)
    
    # Tableau
    tab_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(8.2), Inches(1.5), Inches(1.5), Inches(1.2))
    tab_box.fill.solid()
    tab_box.fill.fore_color.rgb = WHITE
    tab_box.line.color.rgb = GREY
    try:
        tab_box.line.dash_style = 2
    except:
        pass
        
    tx_tab = slide.shapes.add_textbox(Inches(8.2), Inches(1.6), Inches(1.5), Inches(1.0))
    p = tx_tab.text_frame.paragraphs[0]
    p.text = "+ tableau\n\nReporting"
    p.alignment = PP_ALIGN.CENTER
    set_font(p.runs[0], size=10, bold=True)

    # Data flow arrows
    slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(1.5), Inches(2.3), Inches(0.8), Inches(0.15))
    slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(1.5), Inches(3.7), Inches(0.8), Inches(0.15))
    slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(1.5), Inches(5.1), Inches(0.8), Inches(0.15))
    
    slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(4.5), Inches(2.9), Inches(2.2), Inches(0.15)) # to Synapse
    slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(4.5), Inches(1.8), Inches(0.7), Inches(0.15)) # to SQL
    
    slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(6.4), Inches(2.2), Inches(0.6), Inches(0.15)) # SQL to Synapse
    slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(9.0), Inches(2.6), Inches(0.5), Inches(0.15)) # Synapse to Tableau

    # Legend
    leg_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(7.5), Inches(6.0), Inches(2.2), Inches(1.2))
    leg_box.fill.solid()
    leg_box.fill.fore_color.rgb = RGBColor(250, 240, 230)
    leg_box.line.color.rgb = ORANGE
    p = leg_box.text_frame.paragraphs[0]
    p.text = "Legend\nDaily\n3 hours Batch\nOne time"
    set_font(p.runs[0], size=9)


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
    p_pre.text = "IT SOLUTION PROPOSAL"
    set_font(p_pre.runs[0], size=14, bold=True, color=GOLD)
    
    p_main = tf.add_paragraph()
    p_main.text = safe_text(data.get("proposal_title", "Autonomous Solution Design"))
    set_font(p_main.runs[0], size=36, bold=True, color=WHITE)
    
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

    # ----------------------------------------------------
    # SLIDE 3: Capability Gaps & Mitigations
    # ----------------------------------------------------
    slide = prs.slides.add_slide(blank_slide_layout)
    create_slide_header(slide, "Capability Gaps & Mitigations", "Identified gaps against RFP requirements and proposed mitigations")
    add_footer(slide)

    gap_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(1.3), Inches(9.0), Inches(5.5))
    gap_box.fill.solid()
    gap_box.fill.fore_color.rgb = OFF_WHITE
    gap_box.line.color.rgb = CHARCOAL
    gap_box.line.width = Pt(1)

    gap_title = slide.shapes.add_textbox(Inches(0.6), Inches(1.4), Inches(8.8), Inches(5.2))
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
    # SLIDE 3B: High Level Design: Data Flow (Custom Architecture Diagram)
    # ----------------------------------------------------
    slide = prs.slides.add_slide(blank_slide_layout)
    
    # Dark background
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(10), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = RGBColor(15, 15, 15)
    bg.line.fill.background()
    
    # Title
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(9), Inches(0.8))
    p_title = title_box.text_frame.paragraphs[0]
    p_title.text = "High Level Design: Data Flow"
    set_font(p_title.runs[0], size=28, bold=True, color=WHITE)

    # Dynamic Data Flow Layers
    data_flow_items = data.get("data_flow", [])
    if data_flow_items:
        num_items = len(data_flow_items)
        
        # Calculate available height
        start_top = 1.2
        end_bottom = 7.0
        total_avail = end_bottom - start_top
        
        arrow_h = 0.3
        
        # Calculate dynamic box height to fit all items perfectly
        box_h = (total_avail - ((num_items - 1) * arrow_h)) / num_items
        
        # Fallback if too many items
        if box_h < 0.4:
            box_h = 0.4
            arrow_h = 0.1
            
        current_top = start_top
        
        for i, item_text in enumerate(data_flow_items):
            # Draw Box
            box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(current_top), Inches(9.0), Inches(box_h))
            box.fill.solid()
            box.fill.fore_color.rgb = RGBColor(30, 30, 30)
            box.line.color.rgb = RGBColor(120, 120, 120)
            box.line.width = Pt(1.5)
            
            # Text inside box
            tb = slide.shapes.add_textbox(Inches(0.6), Inches(current_top), Inches(8.8), Inches(box_h))
            tf = tb.text_frame
            tf.word_wrap = True
            try:
                tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            except:
                pass
            p = tf.paragraphs[0]
            p.text = safe_text(item_text)
            p.alignment = PP_ALIGN.CENTER
            set_font(p.runs[0], size=11, bold=True, color=WHITE)
            
            current_top += box_h
            
            # Draw downward arrow if not the last item
            if i < num_items - 1:
                arr = slide.shapes.add_textbox(Inches(4.8), Inches(current_top), Inches(0.4), Inches(arrow_h))
                pa = arr.text_frame.paragraphs[0]
                pa.text = "▼"
                pa.alignment = PP_ALIGN.CENTER
                set_font(pa.runs[0], size=12, bold=True, color=ORANGE)
                current_top += arrow_h

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
        
        # Add downward arrow if not the last layer
        if i < len(arch_layers[:4]) - 1:
            arr = slide.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(1.6), top + Inches(1.05), Inches(0.3), Inches(0.2))
            arr.fill.solid()
            arr.fill.fore_color.rgb = ORANGE
            arr.line.fill.background()

        
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
                
                tf_comp = c_box.text_frame
                tf_comp.word_wrap = True
                try:
                    tf_comp.vertical_anchor = MSO_ANCHOR.MIDDLE
                except:
                    pass
                p_comp = tf_comp.paragraphs[0]
                p_comp.text = safe_text(comp)
                p_comp.alignment = PP_ALIGN.CENTER
                set_font(p_comp.runs[0], size=7.5, bold=True, color=CHARCOAL)
                
                # Add horizontal arrow to next component to show sequence
                if j < len(comps) - 1:
                    arr_x = c_left + c_width - Inches(0.15)
                    arr_y = top + Inches(0.4)
                    c_arr = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, arr_x, arr_y, Inches(0.15), Inches(0.2))
                    c_arr.fill.solid()
                    c_arr.fill.fore_color.rgb = ORANGE
                    c_arr.line.fill.background()

    # ----------------------------------------------------
    # SLIDE 4B: Azure Cost Calculator (Estimations)
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
        
        i_headers = ["Azure Component", "Specification", "Est. Monthly Cost"]
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
    # SLIDE 5: Project Milestones
    # ----------------------------------------------------
    slide = prs.slides.add_slide(blank_slide_layout)
    create_slide_header(slide, "Project Milestones", "Sequential delivery phases and target deliverables")
    add_footer(slide)

    phases = data.get("timeline_phases", [
        {"phase": "Design & Planning", "deliverables": "RFP requirements analysis"},
        {"phase": "Development", "deliverables": "Core engineering & integration"},
        {"phase": "Testing", "deliverables": "QA and Integration Testing"},
        {"phase": "Deployment", "deliverables": "Production release"},
        {"phase": "Training", "deliverables": "User training & handover"}
    ])

    enforced_names = ["Design & Planning", "Development", "Testing", "Deployment", "Training"]

    for i, phase in enumerate(phases[:5]):
        top = Inches(1.5 + (i * 1.1))
        
        # Enforce exact phase name
        if i < len(enforced_names):
            phase_name = enforced_names[i]
        else:
            phase_name = safe_text(phase.get("phase", ""))
        
        # Chevron Phase Box
        c_shape = slide.shapes.add_shape(MSO_SHAPE.CHEVRON, Inches(0.5), top, Inches(3.2), Inches(0.9))
        c_shape.fill.solid()
        c_shape.fill.fore_color.rgb = ORANGE
        c_shape.line.fill.background()
        
        # Chevron Text
        tf_c = c_shape.text_frame
        tf_c.word_wrap = True
        p_c = tf_c.paragraphs[0]
        p_c.text = phase_name
        p_c.alignment = PP_ALIGN.CENTER
        set_font(p_c.runs[0], size=11, bold=True, color=WHITE)

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
    # SLIDE 5B: Case Study
    # ----------------------------------------------------
    sim_projects = data.get("similar_projects", [])
    
    if sim_projects:
        for proj in sim_projects:
            slide = prs.slides.add_slide(blank_slide_layout)
            create_slide_header(slide, "Case Study", "Past credentials and successful delivery outcomes")
            add_footer(slide)
            
            p_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(2.0), Inches(8.0), Inches(4.0))
            p_box.fill.solid()
            p_box.fill.fore_color.rgb = OFF_WHITE
            p_box.line.color.rgb = GOLD
            p_box.line.width = Pt(1.5)
            
            tf_p = p_box.text_frame
            tf_p.word_wrap = True
            
            p_title = tf_p.paragraphs[0]
            p_title.text = f"{safe_text(proj.get('client_industry', 'Industry'))} | {safe_text(proj.get('project_name', 'Project'))}"
            set_font(p_title.runs[0], size=20, bold=True, color=ORANGE)
            
            p_outcome = tf_p.add_paragraph()
            p_outcome.text = f"\nOutcome: {safe_text(proj.get('outcome', ''))}"
            set_font(p_outcome.runs[0], size=16, color=CHARCOAL)

    # ----------------------------------------------------
    # SLIDE 6: Effort & Person-Hour Conversion
    # ----------------------------------------------------
    slide = prs.slides.add_slide(blank_slide_layout)
    create_slide_header(slide, "Effort & Person-Hour Conversion", "Allocated program FTE structure, rate cards, and financial sizing")
    add_footer(slide)

    # Table layout
    resources = data.get("resources", [
        {"role": "Engagement Partner", "fte": "0.25", "rate": "$30,000", "total": "$45,000", "person_days": 10},
        {"role": "Lead Architect", "fte": "1.00", "rate": "$24,000", "total": "$144,000", "person_days": 60},
        {"role": "Senior Frontend Developer", "fte": "2.00", "rate": "$8,000", "total": "$96,000", "person_days": 120},
        {"role": "Senior Backend Developer", "fte": "2.00", "rate": "$8,000", "total": "$96,000", "person_days": 120},
        {"role": "DevOps & Security Specialist", "fte": "1.00", "rate": "$9,000", "total": "$54,000", "person_days": 60}
    ])
    
    rows = len(resources) + 2  # +1 for header, +1 for Total Assumption
    # Cap rows to fit on one slide
    rows = min(rows, 9)
    cols = 5
    
    # Calculate a sensible height for the table depending on rows
    table_height = Inches(0.4 * rows)
    table_shape = slide.shapes.add_table(rows, cols, Inches(0.5), Inches(1.5), Inches(9.0), table_height)
    table = table_shape.table

    # Column Widths
    table.columns[0].width = Inches(3.0) # Role
    table.columns[1].width = Inches(1.3) # Count (FTE)
    table.columns[2].width = Inches(1.5) # Hourly Rate
    table.columns[3].width = Inches(1.3) # Person Days
    table.columns[4].width = Inches(1.9) # Total Sizing

    headers = ["Role / Competency", "FTE Count", "Hourly Rate", "Person Days", "Total Financial Sizing"]
    for j, header in enumerate(headers):
        cell = table.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = CHARCOAL
        p = cell.text_frame.paragraphs[0]
        p.text = safe_text(header)
        p.alignment = PP_ALIGN.CENTER
        set_font(p.runs[0], size=11, bold=True, color=WHITE)

    for i, res in enumerate(resources[:rows-2]):
        row_idx = i + 1
        cols_val = [res.get("role"), res.get("fte"), res.get("rate"), str(res.get("person_days", "N/A")), res.get("total")]
        for j, val in enumerate(cols_val):
            cell = table.cell(row_idx, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if row_idx % 2 == 0 else OFF_WHITE
            p = cell.text_frame.paragraphs[0]
            p.text = safe_text(val)
            p.alignment = PP_ALIGN.CENTER if j > 0 else PP_ALIGN.LEFT
            set_font(p.runs[0], size=10, bold=(j == 0), color=CHARCOAL)
            
    # Add Total Assumption Row
    last_row_idx = rows - 1
    
    total_hourly_rate = 0
    for res in resources[:rows-2]:
        rate_str = res.get("rate", "0")
        try:
            rate_val = float(str(rate_str).replace('$', '').replace(',', '').strip())
            total_hourly_rate += rate_val
        except:
            pass

    for j in range(cols):
        cell = table.cell(last_row_idx, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = ORANGE
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        if j == 0:
            p.text = "Total Assumption"
            p.alignment = PP_ALIGN.LEFT
        elif j == 2:
            p.text = f"${int(total_hourly_rate):,}"
        elif j == 4:
            p.text = str(safe_text(data.get("budget", "N/A")))
        else:
            p.text = " "
        if p.runs:
            set_font(p.runs[0], size=11, bold=True, color=WHITE)

    # ----------------------------------------------------
    # SLIDE 7: Required Skills & Competency Matching
    # ----------------------------------------------------
    slide = prs.slides.add_slide(blank_slide_layout)
    create_slide_header(slide, "Skills Inventory & Competency Mapping", "Required technical capabilities grounded in organizational assets")
    add_footer(slide)

    skills_map = data.get("skills_mapping", [
        {"skill": "React 18, TypeScript, Tailwind", "role": "Frontend Developer", "conf": "[✔]"},
        {"skill": "Flask API, Python Core", "role": "Backend Developer", "conf": "[✔]"},
        {"skill": "MySQL Connector, RAG Store", "role": "Database Architect", "conf": "[✔]"},
        {"skill": "python-pptx Engine", "role": "Orchestrator Agent", "conf": "[✔]"},
        {"skill": "CI/CD & DevOps", "role": "DevOps Engineer", "conf": "[✔]"}
    ])
    
    rows2 = len(skills_map) + 1
    # Cap rows to fit on one slide
    rows2 = min(rows2, 9)
    cols2 = 2
    
    table_height2 = Inches(0.4 * rows2)
    table_shape2 = slide.shapes.add_table(rows2, cols2, Inches(0.5), Inches(1.5), Inches(9.0), table_height2)
    table2 = table_shape2.table

    table2.columns[0].width = Inches(4.5) # Skill Name
    table2.columns[1].width = Inches(4.5) # Target Role

    headers2 = ["Technical Skill", "Target Project Role"]
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
        cols_val = [item.get("skill"), item.get("role")]
        for j, val in enumerate(cols_val):
            cell = table2.cell(row_idx, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if row_idx % 2 == 0 else OFF_WHITE
            p = cell.text_frame.paragraphs[0]
            p.text = safe_text(val)
            p.alignment = PP_ALIGN.LEFT
            set_font(p.runs[0], size=10, bold=(j == 0), color=CHARCOAL)

    # ----------------------------------------------------
    # DYNAMIC COMPLEX ARCHITECTURE DIAGRAMS
    # ----------------------------------------------------
    complex_diagrams = data.get("complex_diagrams", [])
    for diag in complex_diagrams:
        slide = prs.slides.add_slide(blank_slide_layout)
        
        # Background
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(10), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = RGBColor(248, 249, 250)
        bg.line.fill.background()
        
        create_slide_header(slide, safe_text(diag.get("title", "Architecture Diagram")), "Dynamic Architecture generated from AI Payload")
        add_footer(slide)
        
        columns = diag.get("columns", [])
        if not columns:
            continue
            
        # Total width ratios
        total_ratio = sum(col.get("width_ratio", 1.0) for col in columns)
        
        # Working area: Left 0.5, Right 9.5 -> width = 9.0
        # Top 1.2, Bottom 6.8 -> height = 5.6
        avail_width = 9.0
        start_x = 0.5
        
        for col in columns:
            ratio = col.get("width_ratio", 1.0)
            col_width = (ratio / total_ratio) * avail_width
            
            # Draw Column Header
            c_header = slide.shapes.add_textbox(Inches(start_x), Inches(1.0), Inches(col_width - 0.1), Inches(0.4))
            p_ch = c_header.text_frame.paragraphs[0]
            p_ch.text = safe_text(col.get("name", ""))
            p_ch.alignment = PP_ALIGN.CENTER
            set_font(p_ch.runs[0], size=12, bold=True, color=CHARCOAL)
            
            zones = col.get("zones", [])
            if zones:
                zone_h = 5.4 / len(zones)
                current_y = 1.4
                
                for zone in zones:
                    bg_color_str = zone.get("bg_color", "transparent")
                    if bg_color_str == "light_green":
                        fill_color = RGBColor(220, 235, 200)
                    elif bg_color_str == "light_grey":
                        fill_color = RGBColor(230, 230, 230)
                    elif bg_color_str == "light_blue":
                        fill_color = RGBColor(210, 230, 250)
                    elif bg_color_str == "white":
                        fill_color = RGBColor(255, 255, 255)
                    else:
                        fill_color = None
                        
                    if fill_color:
                        z_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(start_x), Inches(current_y), Inches(col_width - 0.1), Inches(zone_h - 0.1))
                        z_box.fill.solid()
                        z_box.fill.fore_color.rgb = fill_color
                        z_box.line.color.rgb = GREY
                        z_box.line.width = Pt(1)
                    else:
                        # transparent dashed border
                        z_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(start_x), Inches(current_y), Inches(col_width - 0.1), Inches(zone_h - 0.1))
                        z_box.fill.background()
                        z_box.line.color.rgb = GREY
                        z_box.line.width = Pt(1)
                        # dash_style 2 is dashed
                        try:
                            z_box.line.dash_style = 2
                        except:
                            pass
                    
                    # Zone Title
                    z_title = slide.shapes.add_textbox(Inches(start_x), Inches(current_y), Inches(col_width - 0.1), Inches(0.3))
                    p_zt = z_title.text_frame.paragraphs[0]
                    p_zt.text = safe_text(zone.get("name", ""))
                    set_font(p_zt.runs[0], size=10, bold=True, color=CHARCOAL)
                    
                    items = zone.get("items", [])
                    if items:
                        # simple vertical or 2x2 grid
                        cols_grid = 2 if len(items) > 3 else 1
                        item_w = (col_width - 0.4) / cols_grid
                        item_h = 0.6
                        
                        for idx, item in enumerate(items):
                            r = idx // cols_grid
                            c = idx % cols_grid
                            ix = start_x + 0.15 + (c * (item_w + 0.1))
                            iy = current_y + 0.4 + (r * (item_h + 0.2))
                            
                            shape_type_str = item.get("shape", "box")
                            if shape_type_str == "database":
                                stype = MSO_SHAPE.CAN
                            elif shape_type_str == "cloud":
                                stype = MSO_SHAPE.CLOUD
                            else:
                                stype = MSO_SHAPE.ROUNDED_RECTANGLE
                                
                            item_box = slide.shapes.add_shape(stype, Inches(ix), Inches(iy), Inches(item_w), Inches(item_h))
                            item_box.fill.solid()
                            item_box.fill.fore_color.rgb = WHITE
                            item_box.line.color.rgb = ORANGE
                            item_box.line.width = Pt(1.5)
                            
                            # Item Text
                            it = slide.shapes.add_textbox(Inches(ix), Inches(iy + item_h/2 - 0.2), Inches(item_w), Inches(0.4))
                            pit = it.text_frame.paragraphs[0]
                            pit.text = safe_text(item.get("name", ""))
                            pit.alignment = PP_ALIGN.CENTER
                            set_font(pit.runs[0], size=9, bold=True, color=CHARCOAL)
                            
                    current_y += zone_h
            
            start_x += col_width

    # ----------------------------------------------------
    # HARDCODED "SAME TO SAME" ARCHITECTURE DIAGRAMS
    # ----------------------------------------------------
    # Slide 8: Reference Architecture
    ref_slide = prs.slides.add_slide(blank_slide_layout)
    add_reference_architecture_slide(ref_slide, prs)

    # Slide 9: Azure Landscape Architecture
    azure_slide = prs.slides.add_slide(blank_slide_layout)
    add_azure_landscape_architecture_slide(azure_slide, prs)

    # Save presentation
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    prs.save(output_path)
    print(f"Presentation saved successfully at: {output_path}")
