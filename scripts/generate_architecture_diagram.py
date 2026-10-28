"""
Generates high-resolution, professional architectural diagram for Slide 3.
Clean vector-like styling with modern color palette, sharp borders, and distinct system layers.
"""

from PIL import Image, ImageDraw, ImageFont
import os

width = 1400
height = 1050

img = Image.new("RGBA", (width, height), (255, 255, 255, 255))
draw = ImageDraw.Draw(img)

# Fonts
font_title = ImageFont.truetype("arial.ttf", 28)
font_layer = ImageFont.truetype("arial.ttf", 17)
font_box_title = ImageFont.truetype("arial.ttf", 19)
font_box_sub = ImageFont.truetype("arial.ttf", 15)

# Color Palette
NAVY = (17, 34, 102, 255)       # #112266
TEAL = (0, 140, 110, 255)      # #008C6E
BLUE = (26, 86, 219, 255)      # #1A56DB
DARK = (34, 34, 34, 255)       # #222222
GRAY = (100, 116, 139, 255)    # #64748B
BG_CARD = (248, 250, 252, 255)  # #F8FAFC
BORDER = (203, 213, 225, 255)   # #CBD5E1

# Draw Header Banner
draw.rectangle([40, 30, width - 40, 95], fill=(241, 245, 249, 255), outline=TEAL, width=2)
draw.text((width // 2, 62), "PRAMAAN-AICTE: END-TO-END DECOUPLED ARCHITECTURE", font=font_title, fill=NAVY, anchor="mm")

def draw_layer_box(y_top, y_bottom, layer_num, layer_name, boxes):
    # Background layer box
    draw.rounded_rectangle([40, y_top, width - 40, y_bottom], radius=12, fill=BG_CARD, outline=BORDER, width=2)
    
    # Layer Label Banner
    lbl_w = 420
    draw.rounded_rectangle([60, y_top - 18, 60 + lbl_w, y_top + 18], radius=6, fill=NAVY, outline=None)
    draw.text((60 + lbl_w // 2, y_top), f"LAYER {layer_num}: {layer_name}", font=font_layer, fill=(255, 255, 255, 255), anchor="mm")
    
    # Draw child boxes inside layer
    n = len(boxes)
    margin_x = 70
    spacing = 25
    total_w = (width - 40) - 60 - margin_x
    box_w = (total_w - (n - 1) * spacing) // n
    
    for i, (b_title, b_lines, tag_color) in enumerate(boxes):
        bx = 65 + i * (box_w + spacing)
        by = y_top + 32
        bw = box_w
        bh = y_bottom - y_top - 46
        
        # Child Box
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=8, fill=(255, 255, 255, 255), outline=tag_color, width=2)
        
        # Tag Header
        draw.rounded_rectangle([bx + 4, by + 4, bx + bw - 4, by + 34], radius=4, fill=tag_color, outline=None)
        draw.text((bx + bw // 2, by + 19), b_title, font=font_box_title, fill=(255, 255, 255, 255), anchor="mm")
        
        # Details
        curr_y = by + 45
        for line in b_lines:
            draw.text((bx + 14, curr_y), line, font=font_box_sub, fill=DARK)
            curr_y += 24

# 1. Client Layer
draw_layer_box(130, 310, 1, "MULTI-TENANT PRESENTATION LAYER", [
    ("Institutional Ingestion Desk", ["• Role: College Nodal Officers", "• Interactive Spreadsheet Sandbox", "• Inline Error Highlighting", "• Staged Batch Quarantine"], BLUE),
    ("AICTE Central Command Center", ["• Role: National Administrators", "• Macro Intake Compliance Radar", "• Duplicate Conflict Hearings", "• Statistical Anomaly Auditing"], NAVY),
    ("Zero-PII Public Verifier", ["• Role: Employers & Regulators", "• Standalone Token Verification", "• Asymmetric QR Code Scanner", "• Zero Student PII Exposed"], TEAL)
])

# Draw Connecting Flow Arrows
def draw_flow_arrow(y1, y2):
    cx = width // 2
    draw.line([(cx, y1), (cx, y2)], fill=TEAL, width=4)
    draw.polygon([(cx - 10, y2 - 12), (cx + 10, y2 - 12), (cx, y2)], fill=TEAL)

draw_flow_arrow(310, 355)

# 2. API & Security Layer
draw_layer_box(355, 535, 2, "FASTAPI API & SECURITY LAYER", [
    ("RBAC & Auth Engine", ["• OAuth2 / JWT Dual-Mode Auth", "• Bcrypt Password Hashing", "• Header Bearer + ?token= URL", "• Tenant Isolation Middleware"], NAVY),
    ("Resilient Header Normalizer", ["• Sub-50ms Fuzzy Column Aliasing", "• Auto-detect Date Formats", "• Course Code Harmonization", "• Zero Manual Column Mapping"], TEAL),
    ("Privacy-by-Design Shield", ["• Keyed HMAC-SHA256 Pepper", "• Dynamic Masking (XXXX-1234)", "• Non-Searchable Plaintext Logs", "• DPDP Act 2023 Compliant"], BLUE)
])

draw_flow_arrow(535, 580)

# 3. Reconciliation Core Layer
draw_layer_box(580, 760, 3, "3-WAY RECONCILIATION ENGINE", [
    ("Tier 1: APAAR Identity Syntax", ["• Verhoeff Checksum Dihedral D5", "• 100% Transcription Detection", "• Mock ABC/DigiLocker Gateway", "• Status: VERIFIED / MISMATCH"], TEAL),
    ("Tier 2: Sanctioned Intake Ceilings", ["• APH 2026-27 Quota Enforcement", "• TFW 5% & EWS 10% Isolation", "• Kashmiri Migrants & NRI 15%", "• Blocks Over-Admission Batches"], NAVY),
    ("Tier 3: Cross-College Collision", ["• Nationwide Multi-Tenant Radar", "• Flags Concurrent Admissions", "• Case CONF-2026-XXXX Auto-Gen", "• Side-by-Side Adjudication"], BLUE)
])

draw_flow_arrow(760, 805)

# 4. Storage & Cryptography Layer
draw_layer_box(805, 985, 4, "DATABASE & CRYPTOGRAPHIC TRUST", [
    ("Supabase PostgreSQL Cloud", ["• Managed Cloud DB (ap-south-1)", "• Transaction Pooler (Port 6543)", "• Row-Level Security (RLS)", "• 20 Relational Normal Tables"], BLUE),
    ("Ed25519 Asymmetric Signer", ["• Curve25519 Digital Signatures", "• Tamper-Proof Signed Receipts", "• High-Density 2D QR Encoders", "• Offline Public Key Verification"], TEAL),
    ("SHA-256 Hash Chain Ledger", ["• Append-Only Immutable Chain", "• Hash_n = SHA256(... || Hash_n-1)", "• Genesis Block 0 to Present", "• Mathematical Non-Repudiation"], NAVY)
])

# Save output
out_path = r"D:\AICTE\artifacts\verification\pramaan_system_architecture.png"
img.save(out_path, "PNG")
print(f"Architecture diagram generated: {out_path}")
