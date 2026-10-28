"""
PRAMAAN-AICTE: Final SIH 2026 Presentation Builder (Optimized Visual Hierarchy)
Reconstructs the presentation according to SIH reference decks (sih-winning-ppt-1.pdf)
and audited codebase facts:
- Exactly 6 slides
- Native editable PowerPoint shapes and text
- Factually verified against actual codebase (64/64 passing tests, 20 tables with RLS)
- Real application screenshots embedded
- Optimized whitespace, font scales, and stage card containers
- No fabricated figures, no exposed secrets, no domain placeholders
"""

import os
import sys
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor

# Professional Color Palette matching SIH Reference 1
NAVY = RGBColor(17, 34, 102)          # #112266 - SIH Official Navy
TEAL = RGBColor(0, 140, 110)         # #008C6E - Government Trust Teal
DARK_BLUE = RGBColor(26, 54, 93)     # #1A365D - Deep Slate Blue
ACCENT_BLUE = RGBColor(26, 86, 219)   # #1A56DB - Royal Tech Blue
ALERT_RED = RGBColor(180, 40, 40)    # #B42828 - Risk Red
CHARCOAL = RGBColor(34, 34, 34)      # #222222 - Text Primary
MUTED_GRAY = RGBColor(100, 116, 139) # #64748B - Text Secondary
BG_CARD = RGBColor(255, 255, 255)    # White Card
BG_TINT = RGBColor(248, 250, 252)    # #F8FAFC
BORDER_COLOR = RGBColor(203, 213, 225) # #CBD5E1 - Slate Border
FOOTER_BLUE = RGBColor(0, 111, 191)  # #006FBF - SIH Footer Blue

TEMPLATE_PATH = r"D:\AICTE\finaldemoppt\SIH2026-IDEA-Presentation-Format.pptx"
OUT_PPTX = r"D:\AICTE\deck\final\PRAMAAN-AICTE_SIH2026_Final.pptx"

def format_slide_header(slide, title_text, team_name="TCE_Yquanto", slide_num=2):
    """Formats top title, team oval badge, SIH logo, and bottom footer strip."""
    for shp in slide.shapes:
        if shp.name == "Title 1":
            shp.left = Inches(1.85)
            shp.top = Inches(0.18)
            shp.width = Inches(8.85)
            shp.height = Inches(0.85)
            tf = shp.text_frame
            tf.word_wrap = True
            tf.clear()
            p = tf.paragraphs[0]
            p.text = title_text
            p.font.name = "Arial"
            p.font.size = Pt(16.5)
            p.font.bold = True
            p.font.color.rgb = NAVY
            p.alignment = PP_ALIGN.LEFT

        elif shp.name.startswith("Oval"):
            shp.left = Inches(0.30)
            shp.top = Inches(0.20)
            shp.width = Inches(1.50)
            shp.height = Inches(0.75)
            tf = shp.text_frame
            tf.word_wrap = False
            tf.margin_left = Inches(0.02)
            tf.margin_right = Inches(0.02)
            tf.clear()
            p = tf.paragraphs[0]
            p.text = team_name
            p.font.name = "Arial"
            p.font.size = Pt(9.5)
            p.font.bold = True
            p.font.color.rgb = NAVY
            p.alignment = PP_ALIGN.CENTER

        elif shp.name.startswith("Footer Placeholder"):
            shp.left = Inches(3.0)
            shp.top = Inches(6.98)
            shp.width = Inches(7.33)
            shp.height = Inches(0.40)
            tf = shp.text_frame
            tf.clear()
            p = tf.paragraphs[0]
            p.text = f"@ {team_name} | Smart India Hackathon 2026"
            p.font.name = "Arial"
            p.font.size = Pt(10)
            p.font.color.rgb = RGBColor(255, 255, 255)
            p.alignment = PP_ALIGN.CENTER

        elif shp.name.startswith("Slide Number Placeholder"):
            shp.left = Inches(11.0)
            shp.top = Inches(6.98)
            shp.width = Inches(1.8)
            shp.height = Inches(0.40)
            tf = shp.text_frame
            tf.clear()
            p = tf.paragraphs[0]
            p.text = str(slide_num)
            p.font.name = "Arial"
            p.font.size = Pt(10)
            p.font.bold = True
            p.font.color.rgb = RGBColor(255, 255, 255)
            p.alignment = PP_ALIGN.RIGHT

    # Remove template's default TextBox 8
    for s in [shp for shp in slide.shapes if shp.name == "TextBox 8"]:
        sp = s._element
        sp.getparent().remove(sp)

def create_card(slide, left, top, width, height, border_color=BORDER_COLOR, bg_color=BG_CARD):
    """Creates a rounded container card."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    card.line.color.rgb = border_color
    card.line.width = Pt(1.2)
    return card

def create_header_badge(slide, left, top, width, height, text, bg_color=NAVY):
    """Creates a colored banner badge for a card."""
    badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    badge.fill.solid()
    badge.fill.fore_color.rgb = bg_color
    badge.line.fill.background()
    tf = badge.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.word_wrap = False
    tf.margin_left = Inches(0.08)
    tf.margin_right = Inches(0.08)
    tf.margin_top = Inches(0.01)
    tf.margin_bottom = Inches(0.01)
    tf.clear()
    p = tf.paragraphs[0]
    p.text = text
    p.font.name = "Arial"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = PP_ALIGN.CENTER
    return badge

def build_presentation():
    print(f"Loading official SIH template: {TEMPLATE_PATH}")
    prs = Presentation(TEMPLATE_PATH)

    # 1. Remove instruction slide 7 (Strict SIH Rule #1: exactly 6 slides)
    if len(prs.slides) >= 7:
        print("Removing instruction slide 7 (strict 6-slide rule)...")
        rId = prs.slides._sldIdLst[6].attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
        del prs.slides._sldIdLst[6]

    # =========================================================================
    # SLIDE 1: TITLE PAGE
    # =========================================================================
    print("Building Slide 1 (Title Page)...")
    s1 = prs.slides[0]

    # Hide default 'TITLE PAGE' subtitle placeholder if present
    for shp in s1.shapes:
        if shp.name.startswith("Subtitle"):
            shp.text_frame.clear()

    for shp in s1.shapes:
        if shp.name == "TextBox 9":
            shp.left = Inches(0.50)
            shp.top = Inches(1.70)
            shp.width = Inches(6.50)
            shp.height = Inches(5.10)
            tf = shp.text_frame
            tf.word_wrap = True
            tf.clear()

            title_rows = [
                ("Problem Statement ID", "SIH26263", NAVY, Pt(13.5), True),
                ("Problem Statement Title", "Development of an APAAR ID-Based Student Data Management and Verification Platform for AICTE-Approved Institutions", DARK_BLUE, Pt(11.5), False),
                ("Theme", "Smart Automation", CHARCOAL, Pt(12), False),
                ("PS Category", "Software", CHARCOAL, Pt(12), False),
                ("Team ID", "TCE_Yquanto", CHARCOAL, Pt(12), False),
                ("Team Name", "TCE_Yquanto (Thiagarajar College of Engineering, Madurai)", NAVY, Pt(12.5), True),
                ("Source Repository", "https://github.com/naveeshpcbin/APAAR-ID-BASED-SYSTEM", TEAL, Pt(11), True),
                ("Architecture Baseline", "Next.js 14 + FastAPI + PostgreSQL (20 Tables, RLS) + Deterministic 3-Way Reconciliation", DARK_BLUE, Pt(10.5), False),
                ("Verification Status", "64/64 Passing Automated Pytest Suite across 14 Verification Gates", TEAL, Pt(10.5), True),
            ]

            for idx, (label, val, val_color, val_size, val_bold) in enumerate(title_rows):
                p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
                p.space_before = Pt(6) if idx > 0 else Pt(0)

                r_lbl = p.add_run()
                r_lbl.text = f"{label}: "
                r_lbl.font.name = "Arial"
                r_lbl.font.size = Pt(11.5)
                r_lbl.font.bold = True
                r_lbl.font.color.rgb = NAVY

                r_val = p.add_run()
                r_val.text = val
                r_val.font.name = "Arial"
                r_val.font.size = val_size
                r_val.font.bold = val_bold
                r_val.font.color.rgb = val_color

    # Add bottom footer strip on Slide 1 matching the deck styling
    footer_bar_1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.0), Inches(6.95), Inches(13.333), Inches(0.55))
    footer_bar_1.fill.solid()
    footer_bar_1.fill.fore_color.rgb = FOOTER_BLUE
    footer_bar_1.line.fill.background()

    tb_f1 = s1.shapes.add_textbox(Inches(3.0), Inches(6.98), Inches(7.33), Inches(0.40))
    tf_f1 = tb_f1.text_frame
    p_f1 = tf_f1.paragraphs[0]
    p_f1.text = "@ TCE_Yquanto | Smart India Hackathon 2026"
    p_f1.font.name = "Arial"
    p_f1.font.size = Pt(10)
    p_f1.font.color.rgb = RGBColor(255, 255, 255)
    p_f1.alignment = PP_ALIGN.CENTER

    tb_n1 = s1.shapes.add_textbox(Inches(11.0), Inches(6.98), Inches(1.8), Inches(0.40))
    tf_n1 = tb_n1.text_frame
    p_n1 = tf_n1.paragraphs[0]
    p_n1.text = "1"
    p_n1.font.name = "Arial"
    p_n1.font.size = Pt(10)
    p_n1.font.bold = True
    p_n1.font.color.rgb = RGBColor(255, 255, 255)
    p_n1.alignment = PP_ALIGN.RIGHT

    # =========================================================================
    # SLIDE 2: PROPOSED SOLUTION: THE PRAMAAN-AICTE RECONCILIATION SYSTEM
    # =========================================================================
    print("Building Slide 2 (Proposed Solution - 3 Problem/Solution Pillars + Command Center)...")
    s2 = prs.slides[1]
    format_slide_header(s2, "PROPOSED SOLUTION: THE PRAMAAN-AICTE RECONCILIATION SYSTEM", slide_num=2)

    # LEFT COLUMN: 3 Structured Cards (Problem Addressed, Implementation, Value)
    left_x = Inches(0.40)
    col_w = Inches(6.15)

    pillar_data = [
        (
            Inches(1.22), Inches(1.52),
            "1. REGULATORY CHALLENGE ADDRESSED",
            DARK_BLUE,
            [
                ("Fragmented Institutional Data", "Divergent college ERP spreadsheet schemas, non-standard column headers, and unverified declarations."),
                ("Reconciliation Bottlenecks", "Difficulties cross-verifying declared enrolments against actual student records and AICTE approval ceilings."),
                ("Intake & Duplicate Risks", "Lack of automated visibility into over-intake breaches, quota diversion, and concurrent multi-college claims.")
            ]
        ),
        (
            Inches(2.88), Inches(1.58),
            "2. WHAT PRAMAAN-AICTE IMPLEMENTS",
            NAVY,
            [
                ("Decoupled Institutional Portals", "Role-separated desks for College submission and Central AICTE regulatory governance."),
                ("Automated Ingestion Desk", "CSV/Excel file parsing with resilient column alias mapping into standard staging rows."),
                ("Deterministic 3-Way Reconciliation", "Pure Python comparison engine cross-checking declarations, staged student records, and approved capacity."),
                ("Persisted Validation Runs", "Stores row-level findings with precise classification: approved, quota breach, syntax error, or duplicate.")
            ]
        ),
        (
            Inches(4.60), Inches(1.55),
            "3. KEY WORKFLOW & GOVERNANCE VALUE",
            TEAL,
            [
                ("Explainable Row-Level Findings", "Direct, transparent feedback explaining specific discrepancy causes without opaque batch rejection."),
                ("Quarantine & Resubmission", "Interactive in-browser quarantine sandbox allowing institutions to correct data before council commit."),
                ("Controlled Central Decisions", "Council review workflow supporting formal decisions: approve, return for correction, or reject."),
                ("Audit Traceability", "Complete validation run history and append-only sequential SHA-256 audit chaining across actions.")
            ]
        )
    ]

    for p_top, p_h, p_title, p_color, p_bullets in pillar_data:
        create_card(s2, left_x, p_top, col_w, p_h)
        create_header_badge(s2, left_x + Inches(0.12), p_top - Inches(0.12), col_w - Inches(0.24), Inches(0.30), p_title, p_color)

        tb = s2.shapes.add_textbox(left_x + Inches(0.12), p_top + Inches(0.20), col_w - Inches(0.24), p_h - Inches(0.24))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        for b_idx, (b_lead, b_text) in enumerate(p_bullets):
            p = tf.paragraphs[0] if b_idx == 0 else tf.add_paragraph()
            p.space_before = Pt(2.5) if b_idx > 0 else Pt(0)

            r_lead = p.add_run()
            r_lead.text = f"• {b_lead}: "
            r_lead.font.name = "Arial"
            r_lead.font.size = Pt(8.5)
            r_lead.font.bold = True
            r_lead.font.color.rgb = p_color

            r_text = p.add_run()
            r_text.text = b_text
            r_text.font.name = "Arial"
            r_text.font.size = Pt(8.2)
            r_text.font.color.rgb = CHARCOAL

    # RIGHT COLUMN: Live Implemented System Showcase (AICTE Apex Command Center)
    right_x = Inches(6.75)
    right_w = Inches(6.15)
    right_h = Inches(4.93)
    create_card(s2, right_x, Inches(1.22), right_w, right_h)
    create_header_badge(s2, right_x + Inches(0.15), Inches(1.10), right_w - Inches(0.30), Inches(0.32), "AICTE CENTRAL APEX COMMAND & RECONCILIATION DASHBOARD", NAVY)

    dash_img = r"D:\AICTE\artifacts\live_screenshots\02_dashboard_overview.png"
    if not os.path.exists(dash_img):
        dash_img = r"D:\AICTE\artifacts\verification\dashboard_overview.png"
    if os.path.exists(dash_img):
        s2.shapes.add_picture(dash_img, right_x + Inches(0.12), Inches(1.48), right_w - Inches(0.24), Inches(3.25))

    # Feature Highlights below dashboard image
    tb_dh = s2.shapes.add_textbox(right_x + Inches(0.12), Inches(4.78), right_w - Inches(0.24), Inches(1.30))
    tf_dh = tb_dh.text_frame
    tf_dh.word_wrap = True
    tf_dh.margin_left = tf_dh.margin_right = tf_dh.margin_top = tf_dh.margin_bottom = 0

    dash_features = [
        ("Central Intake Intelligence", "Live monitoring of sanctioned intake vs enrolled students across B.Tech, MCA, and Diploma."),
        ("Deterministic Review Desk", "Instant identification of seat limit breaches, unverified candidates, and duplicate claims."),
        ("Multi-Tenant Governance", "Seamless institutional isolation between AICTE Central Regulators, DTU Delhi, and COEP Pune.")
    ]
    for df_idx, (df_lead, df_text) in enumerate(dash_features):
        p = tf_dh.paragraphs[0] if df_idx == 0 else tf_dh.add_paragraph()
        p.space_before = Pt(2) if df_idx > 0 else Pt(0)
        r_lead = p.add_run()
        r_lead.text = f"✓ {df_lead}: "
        r_lead.font.name = "Arial"
        r_lead.font.size = Pt(8.5)
        r_lead.font.bold = True
        r_lead.font.color.rgb = TEAL
        r_text = p.add_run()
        r_text.text = df_text
        r_text.font.name = "Arial"
        r_text.font.size = Pt(8.2)
        r_text.font.color.rgb = CHARCOAL

    # Bottom Metric Bar
    pills = [
        (Inches(0.40), "✓ Deterministic Python Core", TEAL),
        (Inches(3.55), "⚖️ 3-Way Cross-Reconciliation", NAVY),
        (Inches(6.75), "🔒 Cryptographic Verification & Audit", DARK_BLUE),
        (Inches(9.95), "🛡️ 64/64 Verified Passing Tests", TEAL)
    ]
    for p_left, p_text, p_color in pills:
        pill = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, p_left, Inches(6.30), Inches(2.95), Inches(0.32))
        pill.fill.solid()
        pill.fill.fore_color.rgb = BG_TINT
        pill.line.color.rgb = p_color
        pill.line.width = Pt(1.2)
        ptf = pill.text_frame
        ptf.vertical_anchor = MSO_ANCHOR.MIDDLE
        ptf.margin_left = ptf.margin_right = 0
        p = ptf.paragraphs[0]
        p.text = p_text
        p.font.name = "Arial"
        p.font.size = Pt(8.5)
        p.font.bold = True
        p.font.color.rgb = p_color
        p.alignment = PP_ALIGN.CENTER

    # =========================================================================
    # SLIDE 3: TECHNICAL APPROACH AND SYSTEM ARCHITECTURE
    # =========================================================================
    print("Building Slide 3 (Technical Approach & Architecture)...")
    s3 = prs.slides[2]
    format_slide_header(s3, "TECHNICAL APPROACH AND SYSTEM ARCHITECTURE", slide_num=3)

    # LEFT COLUMN: 5 Modular Stage Cards
    pipe_left = Inches(0.40)
    pipe_w = Inches(6.15)
    create_card(s3, pipe_left, Inches(1.22), pipe_w, Inches(5.42))
    create_header_badge(s3, pipe_left + Inches(0.15), Inches(1.10), pipe_w - Inches(0.30), Inches(0.32), "5-STAGE RECONCILIATION & GOVERNANCE PIPELINE", NAVY)

    stage_cards = [
        ("STAGE 1: INSTITUTIONAL INGESTION & MAPPING",
         "Institutional user authenticates via JWT; uploads CSV/Excel student admissions file. Header normalizer maps diverse column aliases into standard schema.", TEAL),
        ("STAGE 2: DETERMINISTIC PREFLIGHT SCREENING",
         "Fast preflight validation checks mandatory identifier syntax, field types, and isolates corrupted records into quarantine staging.", DARK_BLUE),
        ("STAGE 3: 3-WAY RECONCILIATION ENGINE",
         "Deterministic Python engine compares staged records against institutional declarations, approved programme capacities, and synthetic reference records.", NAVY),
        ("STAGE 4: FINDINGS PERSISTENCE & SANDBOX",
         "Persists validation run records, row-level error findings, and enables in-browser quarantine sandbox for institutional dispute resolution.", ACCENT_BLUE),
        ("STAGE 5: CENTRAL REVIEW & VERIFICATION PROOFS",
         "AICTE Central reviews batch: approves, returns for correction, or rejects. Generates Ed25519-signed verification receipts and appends SHA-256 audit events.", TEAL)
    ]

    card_start_y = Inches(1.52)
    card_h = Inches(0.92)
    card_gap = Inches(0.08)

    for sc_idx, (sc_title, sc_desc, sc_color) in enumerate(stage_cards):
        sc_top = card_start_y + sc_idx * (card_h + card_gap)
        sc_box = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, pipe_left + Inches(0.15), sc_top, pipe_w - Inches(0.30), card_h)
        sc_box.fill.solid()
        sc_box.fill.fore_color.rgb = BG_TINT
        sc_box.line.color.rgb = BORDER_COLOR
        sc_box.line.width = Pt(1.0)

        tb_sc = s3.shapes.add_textbox(pipe_left + Inches(0.22), sc_top + Inches(0.05), pipe_w - Inches(0.44), card_h - Inches(0.10))
        tf_sc = tb_sc.text_frame
        tf_sc.word_wrap = True
        tf_sc.margin_left = tf_sc.margin_right = tf_sc.margin_top = tf_sc.margin_bottom = 0

        p_t = tf_sc.paragraphs[0]
        r_t = p_t.add_run()
        r_t.text = sc_title
        r_t.font.name = "Arial"
        r_t.font.size = Pt(8.8)
        r_t.font.bold = True
        r_t.font.color.rgb = sc_color

        p_d = tf_sc.add_paragraph()
        p_d.space_before = Pt(2)
        r_d = p_d.add_run()
        r_d.text = sc_desc
        r_d.font.name = "Arial"
        r_d.font.size = Pt(8.2)
        r_d.font.color.rgb = CHARCOAL

    # RIGHT COLUMN TOP: Verified Technology Stack
    rt_x = Inches(6.75)
    rt_w = Inches(6.15)
    create_card(s3, rt_x, Inches(1.22), rt_w, Inches(2.25))
    create_header_badge(s3, rt_x + Inches(0.15), Inches(1.10), rt_w - Inches(0.30), Inches(0.30), "VERIFIED 4-LAYER SYSTEM ARCHITECTURE", DARK_BLUE)

    tb_tech = s3.shapes.add_textbox(rt_x + Inches(0.15), Inches(1.48), rt_w - Inches(0.30), Inches(1.92))
    tf_tech = tb_tech.text_frame
    tf_tech.word_wrap = True
    tf_tech.margin_left = tf_tech.margin_right = tf_tech.margin_top = tf_tech.margin_bottom = 0

    tech_layers = [
        ("Presentation Layer", "Next.js 14 (App Router), TypeScript, Tailwind CSS, Recharts for analytics."),
        ("Application & API", "FastAPI (Modular Monolith), Python 3.10+, Pydantic v2, Uvicorn, 73 endpoints."),
        ("Persistence & Schemas", "SQLAlchemy ORM, PostgreSQL (20 tables with RLS enabled) / SQLite WAL mode."),
        ("Cryptography & Security", "Ed25519 (RFC 8032 signing), Keyed HMAC-SHA256, sequential SHA-256 audit chaining.")
    ]
    for tl_idx, (tl_name, tl_desc) in enumerate(tech_layers):
        p = tf_tech.paragraphs[0] if tl_idx == 0 else tf_tech.add_paragraph()
        p.space_before = Pt(4) if tl_idx > 0 else Pt(0)
        r_n = p.add_run()
        r_n.text = f"• {tl_name}: "
        r_n.font.name = "Arial"
        r_n.font.size = Pt(8.8)
        r_n.font.bold = True
        r_n.font.color.rgb = NAVY
        r_d = p.add_run()
        r_d.text = tl_desc
        r_d.font.name = "Arial"
        r_d.font.size = Pt(8.3)
        r_d.font.color.rgb = CHARCOAL

    # RIGHT COLUMN BOTTOM: Genuine Application Quarantine Sandbox Preview
    create_card(s3, rt_x, Inches(3.60), rt_w, Inches(3.04))
    create_header_badge(s3, rt_x + Inches(0.15), Inches(3.48), rt_w - Inches(0.30), Inches(0.30), "INTERACTIVE QUARANTINE SANDBOX & ROW-LEVEL FINDINGS", TEAL)

    sandbox_img = r"D:\AICTE\artifacts\live_screenshots\07_interactive_spreadsheet_sandbox.png"
    if os.path.exists(sandbox_img):
        s3.shapes.add_picture(sandbox_img, rt_x + Inches(0.12), Inches(3.82), rt_w - Inches(0.24), Inches(2.40))

    tb_sb = s3.shapes.add_textbox(rt_x + Inches(0.12), Inches(6.25), rt_w - Inches(0.24), Inches(0.35))
    tf_sb = tb_sb.text_frame
    tf_sb.word_wrap = True
    p_sb = tf_sb.paragraphs[0]
    p_sb.text = "Genuine Implemented UI: In-browser editable spreadsheet sandbox isolates validation findings before central commit."
    p_sb.font.name = "Arial"
    p_sb.font.size = Pt(7.8)
    p_sb.font.color.rgb = MUTED_GRAY
    p_sb.alignment = PP_ALIGN.CENTER

    # =========================================================================
    # SLIDE 4: FEASIBILITY, VIABILITY AND RISK MITIGATION
    # =========================================================================
    print("Building Slide 4 (Feasibility, Viability & Risk Mitigation)...")
    s4 = prs.slides[3]
    format_slide_header(s4, "FEASIBILITY, VIABILITY AND RISK MITIGATION", slide_num=4)

    # LEFT COLUMN: Feasibility & Implementation Maturity
    f_left = Inches(0.40)
    f_w = Inches(6.15)
    f_h = Inches(5.42)
    create_card(s4, f_left, Inches(1.22), f_w, f_h)
    create_header_badge(s4, f_left + Inches(0.15), Inches(1.10), f_w - Inches(0.30), Inches(0.32), "IMPLEMENTATION FEASIBILITY & VERIFIED MATURITY", NAVY)

    tb_feas = s4.shapes.add_textbox(f_left + Inches(0.15), Inches(1.50), f_w - Inches(0.30), Inches(5.00))
    tf_feas = tb_feas.text_frame
    tf_feas.word_wrap = True
    tf_feas.margin_left = tf_feas.margin_right = tf_feas.margin_top = tf_feas.margin_bottom = 0

    feas_points = [
        ("Architectural Feasibility", "Zero-install web architecture. Standard modern browser access across Windows, Linux, and macOS. Decoupled Next.js client and FastAPI modular backend."),
        ("Verified Test Suite (64/64 Passing)", "Exhaustive automated verification across 14 test suites covering authentication, institution onboarding, batch upload, deterministic reconciliation, security, and reference data."),
        ("Deterministic Logic Integrity", "Reconciliation logic is pure, explainable Python with explicit rule sets for sanctioned intake and supernumerary quotas; avoids opaque or non-deterministic AI decisions."),
        ("Synthetic Data Testing Engine", "Database-backed synthetic APAAR identities and editable approval/declaration models enable comprehensive pre-deployment stress testing and repeatable verification."),
        ("Dual-Dialect Database Support", "SQLAlchemy ORM architecture with dynamic driver fallback (psycopg3/psycopg2) verified on local SQLite WAL mode and configured PostgreSQL schemas (20 tables, RLS active)."),
        ("Transparent Deployment Status", "Application codebase, schemas, and test suites 100% verified locally; cloud Render web deployment is currently pending resolution of cloud environment DNS configuration.")
    ]

    for fp_idx, (fp_lead, fp_text) in enumerate(feas_points):
        p = tf_feas.paragraphs[0] if fp_idx == 0 else tf_feas.add_paragraph()
        p.space_before = Pt(7.5) if fp_idx > 0 else Pt(0)
        r_lead = p.add_run()
        r_lead.text = f"• {fp_lead}: "
        r_lead.font.name = "Arial"
        r_lead.font.size = Pt(8.9)
        r_lead.font.bold = True
        r_lead.font.color.rgb = DARK_BLUE
        r_text = p.add_run()
        r_text.text = fp_text
        r_text.font.name = "Arial"
        r_text.font.size = Pt(8.4)
        r_text.font.color.rgb = CHARCOAL

    # RIGHT COLUMN: Governance Risks & Technical Countermeasures
    r_left = Inches(6.75)
    r_w = Inches(6.15)
    create_card(s4, r_left, Inches(1.22), r_w, f_h)
    create_header_badge(s4, r_left + Inches(0.15), Inches(1.10), r_w - Inches(0.30), Inches(0.32), "GOVERNANCE RISKS & TECHNICAL COUNTERMEASURES", ALERT_RED)

    tb_risk = s4.shapes.add_textbox(r_left + Inches(0.15), Inches(1.50), r_w - Inches(0.30), Inches(5.00))
    tf_risk = tb_risk.text_frame
    tf_risk.word_wrap = True
    tf_risk.margin_left = tf_risk.margin_right = tf_risk.margin_top = tf_risk.margin_bottom = 0

    risks = [
        ("Risk: Inconsistent Institutional Spreadsheets", "Colleges use varying ERP schemas and column headers (e.g. apaar_id vs uid vs student_apaar).",
         "Header alias normalizer maps 50+ divergent column variants into standard canonical schema automatically."),
        ("Risk: Student Identifier Privacy Exposure", "Storing plaintext 12-digit student APAAR identifiers risks data leakage under DPDP Act 2023.",
         "Keyed HMAC-SHA256 pseudonymized indexing and dynamic masking (XXXX-XXXX-9012) ensure zero plaintext PII exposure."),
        ("Risk: Multi-Institution Concurrent Admissions", "Students admitted concurrently across different institutions leading to seat blocking.",
         "Cross-institution collision radar cross-checks active admissions against centralized reference records and flags duplicates."),
        ("Risk: Regulatory Non-Repudiation & Tampering", "Unauthorized insider tampering with approved intake capacity or admission records.",
         "Append-only sequential SHA-256 hash chaining (Hash_n = SHA256(Record_n || Hash_n-1)) mathematically exposes any tampering."),
        ("Risk: Database Driver & Cloud Hosting Mismatch", "Container deployment failures caused by PostgreSQL driver compatibility or DNS misconfiguration.",
         "Implemented psycopg3/psycopg2 dynamic driver fallback with automated fallback logging and sanitized connection strings.")
    ]

    for r_idx, (r_title, r_desc, r_mit) in enumerate(risks):
        p_t = tf_risk.paragraphs[0] if r_idx == 0 else tf_risk.add_paragraph()
        p_t.space_before = Pt(6) if r_idx > 0 else Pt(0)
        r_t = p_t.add_run()
        r_t.text = f"⚠️ {r_title}: "
        r_t.font.name = "Arial"
        r_t.font.size = Pt(8.7)
        r_t.font.bold = True
        r_t.font.color.rgb = ALERT_RED
        r_td = p_t.add_run()
        r_td.text = r_desc
        r_td.font.name = "Arial"
        r_td.font.size = Pt(8.2)
        r_td.font.color.rgb = CHARCOAL

        p_m = tf_risk.add_paragraph()
        p_m.space_before = Pt(1.5)
        r_m = p_m.add_run()
        r_m.text = f"  → Control: "
        r_m.font.name = "Arial"
        r_m.font.size = Pt(8.5)
        r_m.font.bold = True
        r_m.font.color.rgb = TEAL
        r_md = p_m.add_run()
        r_md.text = r_mit
        r_md.font.name = "Arial"
        r_md.font.size = Pt(8.2)
        r_md.font.color.rgb = CHARCOAL

    # =========================================================================
    # SLIDE 5: IMPACT AND BENEFITS
    # =========================================================================
    print("Building Slide 5 (Impact and Benefits)...")
    s5 = prs.slides[4]
    format_slide_header(s5, "MULTI-STAKEHOLDER IMPACT & DEGREE VERIFICATION", slide_num=5)

    # LEFT COLUMN: Multi-Stakeholder Impact
    imp_left = Inches(0.40)
    imp_w = Inches(6.15)
    imp_h = Inches(5.42)
    create_card(s5, imp_left, Inches(1.22), imp_w, imp_h)
    create_header_badge(s5, imp_left + Inches(0.15), Inches(1.10), imp_w - Inches(0.30), Inches(0.32), "MULTI-STAKEHOLDER REGULATORY IMPACT", TEAL)

    tb_imp = s5.shapes.add_textbox(imp_left + Inches(0.15), Inches(1.50), imp_w - Inches(0.30), Inches(5.00))
    tf_imp = tb_imp.text_frame
    tf_imp.word_wrap = True
    tf_imp.margin_left = tf_imp.margin_right = tf_imp.margin_top = tf_imp.margin_bottom = 0

    stakeholders = [
        ("AICTE & Regulatory Councils", "Comprehensive real-time visibility into institutional enrolment versus sanctioned intake quotas; early detection of unauthorized excess enrolments and quota breaches."),
        ("Approved Institutions", "Standardized data submission, instant row-level discrepancy explanations, and controlled resubmission workflows replacing prolonged paper audit cycles."),
        ("Students & Deserving Candidates", "Transparent tracking protects legitimate seat allocations and safeguards affirmative action quotas from unauthorized commercial reallocation."),
        ("Academic Verifiers & Employers", "Fast offline verification via QR code and cryptographically signed verification receipts without requiring manual institutional registrar confirmation."),
        ("Social Equity & Affirmative Action", "Rigorous enforcement of statutory and supernumerary quotas (TFW, EWS, Kashmiri Migrants) against arbitrary substitution."),
        ("Administrative & Paperless Efficiency", "100% digital data reconciliation replaces manual paperwork, physical affidavits, and physical institutional auditing logistics.")
    ]

    for sh_idx, (sh_name, sh_desc) in enumerate(stakeholders):
        p = tf_imp.paragraphs[0] if sh_idx == 0 else tf_imp.add_paragraph()
        p.space_before = Pt(7.5) if sh_idx > 0 else Pt(0)
        r_name = p.add_run()
        r_name.text = f"• {sh_name}: "
        r_name.font.name = "Arial"
        r_name.font.size = Pt(8.9)
        r_name.font.bold = True
        r_name.font.color.rgb = DARK_BLUE
        r_desc = p.add_run()
        r_desc.text = sh_desc
        r_desc.font.name = "Arial"
        r_desc.font.size = Pt(8.4)
        r_desc.font.color.rgb = CHARCOAL

    # RIGHT COLUMN: SIH Requirement 10: Degree Certificate Verification
    cert_left = Inches(6.75)
    cert_w = Inches(6.15)
    create_card(s5, cert_left, Inches(1.22), cert_w, imp_h)
    create_header_badge(s5, cert_left + Inches(0.15), Inches(1.10), cert_w - Inches(0.30), Inches(0.32), "SIH REQUIREMENT 10: DEGREE CERTIFICATE VERIFICATION", NAVY)

    cert_img = r"D:\AICTE\artifacts\live_screenshots\08_student_certificate_verified.png"
    if not os.path.exists(cert_img):
        cert_img = r"D:\AICTE\artifacts\verification\student_certificate_verified.png"
    if os.path.exists(cert_img):
        s5.shapes.add_picture(cert_img, cert_left + Inches(0.12), Inches(1.48), cert_w - Inches(0.24), Inches(3.20))

    # Certificate Details & Verification Features
    tb_cd = s5.shapes.add_textbox(cert_left + Inches(0.12), Inches(4.78), cert_w - Inches(0.24), Inches(1.75))
    tf_cd = tb_cd.text_frame
    tf_cd.word_wrap = True
    tf_cd.margin_left = tf_cd.margin_right = tf_cd.margin_top = tf_cd.margin_bottom = 0

    cert_features = [
        ("Dual Identity Display", "Certificates present Student Enrolment Roll No (ENR-108410E1) alongside masked APAAR ID (XXXXXXXX7890) and category quota status."),
        ("Asymmetric Ed25519 QR Code", "Embedded high-density QR code carries a digitally signed verification token; verifiers validate data integrity against AICTE public key offline."),
        ("Integrity Boundary Clarification", "Digital signature confirms platform-level record integrity and non-tampering; explicitly distinguished from official government identity confirmation.")
    ]
    for cf_idx, (cf_lead, cf_text) in enumerate(cert_features):
        p = tf_cd.paragraphs[0] if cf_idx == 0 else tf_cd.add_paragraph()
        p.space_before = Pt(3) if cf_idx > 0 else Pt(0)
        r_lead = p.add_run()
        r_lead.text = f"✓ {cf_lead}: "
        r_lead.font.name = "Arial"
        r_lead.font.size = Pt(8.6)
        r_lead.font.bold = True
        r_lead.font.color.rgb = TEAL
        r_text = p.add_run()
        r_text.text = cf_text
        r_text.font.name = "Arial"
        r_text.font.size = Pt(8.2)
        r_text.font.color.rgb = CHARCOAL

    # =========================================================================
    # SLIDE 6: RESEARCH, REFERENCES AND PROJECT RESOURCES
    # =========================================================================
    print("Building Slide 6 (Research, References & Resources)...")
    s6 = prs.slides[5]
    format_slide_header(s6, "RESEARCH, REFERENCES AND PROJECT RESOURCES", slide_num=6)

    # LEFT COLUMN: Authoritative Standards & Regulatory References
    ref_left = Inches(0.40)
    ref_w = Inches(6.15)
    ref_h = Inches(5.42)
    create_card(s6, ref_left, Inches(1.22), ref_w, ref_h)
    create_header_badge(s6, ref_left + Inches(0.15), Inches(1.10), ref_w - Inches(0.30), Inches(0.32), "AUTHORITATIVE STANDARDS & REGULATORY CITATIONS", NAVY)

    tb_ref = s6.shapes.add_textbox(ref_left + Inches(0.15), Inches(1.50), ref_w - Inches(0.30), Inches(5.00))
    tf_ref = tb_ref.text_frame
    tf_ref.word_wrap = True
    tf_ref.margin_left = tf_ref.margin_right = tf_ref.margin_top = tf_ref.margin_bottom = 0

    citations = [
        ("AICTE Approval Process Handbook (APH 2026-27)",
         "Statutory norms for approved institutional intake capacity, supernumerary seat limits (TFW, EWS, Kashmiri Migrants), and programme approval guidelines."),
        ("National Education Policy (NEP 2020) & APAAR / ABC",
         "Government policy framework establishing the 12-digit Automated Permanent Academic Account Registry as the lifelong national academic identifier."),
        ("Digital Personal Data Protection Act (DPDP Act 2023)",
         "Data fiduciary compliance, purpose limitation, identifier pseudonymization, dynamic masking, and student consent management frameworks."),
        ("IETF RFC 8032: Ed25519 Cryptography",
         "Specification for Edwards-Curve Digital Signature Algorithm (Curve25519) providing mathematical non-repudiation and instant receipt verification."),
        ("NIST SP 800-107: Recommendation for Secure Hashing",
         "Cryptographic guidelines for sequential SHA-256 hash chaining utilized in the tamper-evident regulatory audit trail.")
    ]

    for c_idx, (c_title, c_desc) in enumerate(citations):
        p_t = tf_ref.paragraphs[0] if c_idx == 0 else tf_ref.add_paragraph()
        p_t.space_before = Pt(8) if c_idx > 0 else Pt(0)
        r_t = p_t.add_run()
        r_t.text = f"• {c_title}"
        r_t.font.name = "Arial"
        r_t.font.size = Pt(9.0)
        r_t.font.bold = True
        r_t.font.color.rgb = DARK_BLUE

        p_d = tf_ref.add_paragraph()
        p_d.space_before = Pt(2)
        r_d = p_d.add_run()
        r_d.text = c_desc
        r_d.font.name = "Arial"
        r_d.font.size = Pt(8.4)
        r_d.font.color.rgb = CHARCOAL

    # RIGHT COLUMN TOP: Scope Differentiation (Prior Art vs PRAMAAN-AICTE)
    res_left = Inches(6.75)
    res_w = Inches(6.15)
    create_card(s6, res_left, Inches(1.22), res_w, Inches(2.60))
    create_header_badge(s6, res_left + Inches(0.15), Inches(1.10), res_w - Inches(0.30), Inches(0.30), "SCOPE DIFFERENTIATION (PRIOR ART VS PRAMAAN-AICTE)", TEAL)

    tb_diff = s6.shapes.add_textbox(res_left + Inches(0.15), Inches(1.48), res_w - Inches(0.30), Inches(2.25))
    tf_diff = tb_diff.text_frame
    tf_diff.word_wrap = True
    tf_diff.margin_left = tf_diff.margin_right = tf_diff.margin_top = tf_diff.margin_bottom = 0

    diff_points = [
        ("Validation Scope", "Generic uploads check syntax only. PRAMAAN performs 3-way reconciliation (Declarations × Uploads × Sanctioned Capacity)."),
        ("Reference Data", "Traditional workflows rely on static assumptions. PRAMAAN integrates dynamic database references with revalidation."),
        ("Finding Resolution", "Standard systems use opaque batch rejections. PRAMAAN provides row-level explainable findings and an editable quarantine sandbox."),
        ("Verification Output", "Conventional portals yield unverified spreadsheets. PRAMAAN produces Ed25519-signed verification receipts and QR proofs.")
    ]
    for d_idx, (d_lead, d_text) in enumerate(diff_points):
        p = tf_diff.paragraphs[0] if d_idx == 0 else tf_diff.add_paragraph()
        p.space_before = Pt(3.5) if d_idx > 0 else Pt(0)
        r_l = p.add_run()
        r_l.text = f"• {d_lead}: "
        r_l.font.name = "Arial"
        r_l.font.size = Pt(8.5)
        r_l.font.bold = True
        r_l.font.color.rgb = NAVY
        r_t = p.add_run()
        r_t.text = d_text
        r_t.font.name = "Arial"
        r_t.font.size = Pt(8.1)
        r_t.font.color.rgb = CHARCOAL

    # RIGHT COLUMN BOTTOM: Verified Project Resources & Environment Status
    create_card(s6, res_left, Inches(3.95), res_w, Inches(2.69))
    create_header_badge(s6, res_left + Inches(0.15), Inches(3.82), res_w - Inches(0.30), Inches(0.30), "VERIFIED PROJECT RESOURCES & ENVIRONMENT STATUS", DARK_BLUE)

    tb_res = s6.shapes.add_textbox(res_left + Inches(0.15), Inches(4.20), res_w - Inches(0.30), Inches(2.35))
    tf_res = tb_res.text_frame
    tf_res.word_wrap = True
    tf_res.margin_left = tf_res.margin_right = tf_res.margin_top = tf_res.margin_bottom = 0

    resources = [
        ("Open-Source GitHub Repository", "https://github.com/naveeshpcbin/APAAR-ID-BASED-SYSTEM\n(Complete source code, 20 application models, Alembic migrations, test suites)"),
        ("Interactive Backend API Docs", "FastAPI OpenAPI 3.1 documentation available at `/docs` (73 endpoints registered across 67 paths)."),
        ("Automated Test Verification", "64/64 pytest automated tests passing locally across 14 test suites covering all core workflows."),
        ("System Integration Status", "• External APAAR / DigiLocker / ABC API: SIMULATED (Synthetic reference dataset).\n• Cloud Render Deployment: PENDING RESOLUTION (Host DNS configuration in Render container).")
    ]

    for rs_idx, (rs_title, rs_desc) in enumerate(resources):
        p = tf_res.paragraphs[0] if rs_idx == 0 else tf_res.add_paragraph()
        p.space_before = Pt(3.5) if rs_idx > 0 else Pt(0)
        r_tl = p.add_run()
        r_tl.text = f"✓ {rs_title}: "
        r_tl.font.name = "Arial"
        r_tl.font.size = Pt(8.5)
        r_tl.font.bold = True
        r_tl.font.color.rgb = TEAL
        r_ds = p.add_run()
        r_ds.text = rs_desc
        r_ds.font.name = "Arial"
        r_ds.font.size = Pt(8.1)
        r_ds.font.color.rgb = CHARCOAL

    # Save final PPTX
    os.makedirs(os.path.dirname(OUT_PPTX), exist_ok=True)
    print(f"Saving final presentation to: {OUT_PPTX}")
    prs.save(OUT_PPTX)
    print("PPTX build complete!")

if __name__ == "__main__":
    build_presentation()
