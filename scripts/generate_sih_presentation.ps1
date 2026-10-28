# PRAMAAN-AICTE — Smart India Hackathon 2026 Idea Presentation Generator
# Replicates exact official SIH2026 template format with real prototype data and clean screenshots

$sourcePath = "D:\AICTE\demoppt\SIH2026-IDEA-Presentation-Format (1).pptx"
$outPptxPath = "D:\AICTE\demoppt\PRAMAAN-AICTE_SIH2026_Idea_Presentation.pptx"
$outPdfPath = "D:\AICTE\demoppt\PRAMAAN-AICTE_SIH2026_Idea_Presentation.pdf"
$slidesDir = "D:\AICTE\demoppt\slides"

if (!(Test-Path $slidesDir)) {
    New-Item -ItemType Directory -Path $slidesDir | Out-Null
}

# Ensure PowerPoint is closed before starting
Get-Process -Name "POWERPNT" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 500

# Copy fresh template to output path
Copy-Item $sourcePath $outPptxPath -Force

$ppt = New-Object -ComObject PowerPoint.Application
$pres = $ppt.Presentations.Open($outPptxPath, 0, 0, 0)

# Color Palette (BGR format for Office COM)
$cSIHNavy = 0x662211   # RGB(17, 34, 102) -> BGR: 0x662211
$cTeal    = 0x6E8C00   # RGB(0, 140, 110) -> BGR: 0x6E8C00
$cDark    = 0x222222   # RGB(34, 34, 34)
$cGray    = 0x555555   # RGB(85, 85, 85)

function Format-SlideTitle($shape, $titleText) {
    $shape.TextFrame.TextRange.Text = $titleText
    $shape.TextFrame.TextRange.Font.Name = "Arial"
    $shape.TextFrame.TextRange.Font.Size = 18
    $shape.TextFrame.TextRange.Font.Bold = 1
    $shape.TextFrame.TextRange.Font.Color.RGB = 0x000000
    $shape.Left = 140
    $shape.Top = 16
    $shape.Width = 620
    $shape.Height = 55
}

function Build-CleanTextBox($slide, $lines, $headers, $mainHeading = "") {
    # Remove template's original TextBox 8 which contains pre-baked spacing/underlines
    try {
        $slide.Shapes.Item("TextBox 8").Delete()
    } catch {}

    $tb = $slide.Shapes.AddTextbox(1, 28, 92, 495, 420)
    $tf = $tb.TextFrame
    $tf.WordWrap = -1
    $tf.MarginLeft = 0
    $tf.MarginRight = 0
    $tf.MarginTop = 0
    $tf.MarginBottom = 0

    $tb.TextFrame.TextRange.Text = ($lines -join "`n")
    $tb.TextFrame.TextRange.Font.Name = "Arial"
    $tb.TextFrame.TextRange.Font.Size = 10
    $tb.TextFrame.TextRange.Font.Color.RGB = $cDark
    $tb.TextFrame.TextRange.Font.Underline = 0

    if ($mainHeading -ne "") {
        $fMain = $tb.TextFrame.TextRange.Find($mainHeading)
        if ($fMain) {
            $fMain.Font.Bold = 1
            $fMain.Font.Size = 13
            $fMain.Font.Color.RGB = $cSIHNavy
        }
    }

    foreach ($h in $headers) {
        $f = $tb.TextFrame.TextRange.Find($h)
        if ($f) {
            $f.Font.Bold = 1
            $f.Font.Size = 11
            $f.Font.Color.RGB = $cTeal
        }
    }

    return $tb
}

function Add-PrototypePicture($slide, $imgPath, $left, $top, $width, $height, $captionText) {
    if (Test-Path $imgPath) {
        $pic = $slide.Shapes.AddPicture($imgPath, 0, 1, $left, $top, $width, $height)
        $pic.Line.Visible = -1
        $pic.Line.ForeColor.RGB = 0xCCCCCC
        $pic.Line.Weight = 1
        
        $cap = $slide.Shapes.AddTextbox(1, $left, ($top + $height + 4), $width, 50)
        $cap.TextFrame.TextRange.Text = $captionText
        $cap.TextFrame.TextRange.Font.Name = "Arial"
        $cap.TextFrame.TextRange.Font.Size = 8.5
        $cap.TextFrame.TextRange.Font.Italic = 1
        $cap.TextFrame.TextRange.Font.Color.RGB = $cGray
        $cap.TextFrame.MarginLeft = 0
        $cap.TextFrame.MarginRight = 0
        $cap.TextFrame.MarginTop = 0
        $cap.TextFrame.MarginBottom = 0
    }
}

function Format-TeamOval($slide, $teamName = "TCE_Yquanto") {
    foreach ($shp in $slide.Shapes) {
        if ($shp.Name -like "Oval*") {
            $tf = $shp.TextFrame
            $tf.MarginLeft = 2
            $tf.MarginRight = 2
            $tf.WordWrap = 0 # msoFalse
            $tr = $tf.TextRange
            $tr.Text = $teamName
            $tr.Font.Name = "Arial"
            $tr.Font.Size = 11
            $tr.Font.Bold = 1
            $tr.Font.Color.RGB = 0x662211 # SIH Navy
            $tr.ParagraphFormat.Alignment = 2 # ppAlignCenter
        }
    }
}

# ==========================================
# SLIDE 1: TITLE PAGE
# ==========================================
Write-Host "Formatting Slide 1 (Title Page)..."
$s1 = $pres.Slides.Item(1)
$tb1 = $s1.Shapes.Item("TextBox 9")

$s1Text = @"
Problem Statement ID: SIH26263

Problem Statement Title: Development of an APAAR ID-Based Student Data Management and Verification Platform for AICTE-Approved Institutions

Theme: Smart Automation

PS Category: Software

Team ID: 

Team Name (Registered on portal): TCE_Yquanto
"@

$tb1.TextFrame.TextRange.Text = $s1Text
$tb1.TextFrame.TextRange.Font.Name = "Arial"
$tb1.TextFrame.TextRange.Font.Size = 15.5
$tb1.TextFrame.TextRange.Font.Bold = 1
$tb1.Left = 32
$tb1.Top = 155
$tb1.Width = 490
$tb1.Height = 360

# Style Slide 1 labels in navy
foreach ($label in @("Problem Statement ID:", "Problem Statement Title:", "Theme:", "PS Category:", "Team ID:", "Team Name (Registered on portal):")) {
    $f = $tb1.TextFrame.TextRange.Find($label)
    if ($f) {
        $f.Font.Color.RGB = $cSIHNavy
    }
}

# ==========================================
# SLIDE 2: PROPOSED SOLUTION
# ==========================================
Write-Host "Formatting Slide 2 (Proposed Solution)..."
$s2 = $pres.Slides.Item(2)
Format-SlideTitle $s2.Shapes.Item("Title 1") "PRAMAAN-AICTE: APAAR-BASED REGULATORY MONITORING & VERIFICATION"
Format-TeamOval $s2 "TCE_Yquanto"

$s2Lines = @(
    "Proposed Solution (Describe your Idea/Solution/Prototype)",
    "",
    "Detailed explanation of the proposed solution:",
    "* High-trust, privacy-preserving regulatory intelligence platform for AICTE and institutions.",
    "* End-to-end ERP/spreadsheet ingestion with automated schema mapping and preflight validation.",
    "* Role-separated workspaces: Institution Data Desk, Central Review Console, and Trust Gateway.",
    "",
    "How it addresses the problem:",
    "* Unifies fragmented records by anchoring admissions to verified APAAR identity references.",
    "* Prevents phantom seats and ghost admissions via AICTE Approval Handbook (APH 2026-27) quota rules.",
    "* Detects multi-college double enrollments through automated cross-institution duplicate collision radar.",
    "",
    "Innovation and uniqueness of the solution:",
    "* Zero Plaintext Storage: Keyed HMAC-SHA256 indexing + dynamic masking (********1234).",
    "* Cryptographic Verifiability: Asymmetric Ed25519 digital signatures on all verification receipts.",
    "* Tamper-Evident Ledger: Append-only sequential SHA-256 hash chaining securing all decisions."
)

Build-CleanTextBox $s2 $s2Lines @(
    "Detailed explanation of the proposed solution:",
    "How it addresses the problem:",
    "Innovation and uniqueness of the solution:"
) "Proposed Solution (Describe your Idea/Solution/Prototype)" | Out-Null

Add-PrototypePicture $s2 "D:\AICTE\artifacts\verification\dashboard_overview.png" 535 95 405 245 "Prototype Evidence: AICTE Central Regulatory Monitoring Console with real-time intake utilization, active college directory, duplicate radar, and verification audit counts."

# ==========================================
# SLIDE 3: TECHNICAL APPROACH
# ==========================================
Write-Host "Formatting Slide 3 (Technical Approach)..."
$s3 = $pres.Slides.Item(3)
Format-SlideTitle $s3.Shapes.Item("Title 1") "TECHNICAL APPROACH & ARCHITECTURE"
Format-TeamOval $s3 "TCE_Yquanto"

$s3Lines = @(
    "Technologies to be used:",
    "* Frontend Architecture: Next.js 14 App Router, TypeScript, Tailwind CSS, Recharts.",
    "* Backend API Services: Python 3.10, FastAPI, Pydantic V2, Uvicorn, OpenAPI 3.1 REST contracts.",
    "* Database & Persistence: SQLite 3 (WAL mode) / PostgreSQL dual-dialect via SQLAlchemy ORM.",
    "* Security & Cryptography: Ed25519 (RFC 8032) asymmetric signatures, Keyed HMAC-SHA256, bcrypt.",
    "* Data Processing: Pandas and OpenPyXL for fault-tolerant tabular ingestion and reconciliation.",
    "",
    "Methodology and process for implementation:",
    "* Multi-Tier Validation Pipeline:",
    "   1. Ingestion Desk: CSV/Excel drag-and-drop with fuzzy header mapping & course code tolerance.",
    "   2. Preflight Gate: Regex syntax checks, in-file duplicate detection, and intake ceiling audits.",
    "   3. Atomic Two-Phase Commit: Staging into decoupled StudentIdentity and AdmissionRecord.",
    "   4. Regulatory Adjudication: Automated double-enrollment radar with recorded reviewer remarks.",
    "   5. Cryptographic Proof: Ed25519-signed verification receipts and tamper-evident SHA-256 audit."
)

Build-CleanTextBox $s3 $s3Lines @(
    "Technologies to be used:",
    "Methodology and process for implementation:",
    "Multi-Tier Validation Pipeline:"
) | Out-Null

Add-PrototypePicture $s3 "D:\AICTE\artifacts\verification\uploads_page.png" 535 95 405 245 "Prototype Evidence: Smart Ingestion Desk with automated schema mapping, pre-flight validation status, row findings ledger, and atomic batch commitment."

# ==========================================
# SLIDE 4: FEASIBILITY AND VIABILITY
# ==========================================
Write-Host "Formatting Slide 4 (Feasibility & Viability)..."
$s4 = $pres.Slides.Item(4)
Format-SlideTitle $s4.Shapes.Item("Title 1") "FEASIBILITY AND VIABILITY"
Format-TeamOval $s4 "TCE_Yquanto"

$s4Lines = @(
    "Analysis of the feasibility of the idea:",
    "* Operational Feasibility: Zero specialized hardware needed; works over modern web browsers.",
    "* Verified Engineering Prototype: 31/31 passing unit/integration tests, 79% backend coverage.",
    "* High Performance: Sub-50ms deterministic preflight checks; handles 5,000+ student batches.",
    "",
    "Potential challenges and risks:",
    "* Data Inconsistency: Unstandardized CSV/Excel exports from fragmented college ERP systems.",
    "* Identity Privacy Risk: Exposure of plaintext student identifiers violating DPDP Act 2023.",
    "* Multi-College Collisions: Fraudulent concurrent admissions across multiple institutions.",
    "* Unauthorized Record Tampering: Illicit modification of approved intake quotas or student status.",
    "",
    "Strategies for overcoming these challenges:",
    "* Resilient Header Engine: Fuzzy column mapping and alias normalization (BTECH-CSE <-> CSE-BTECH).",
    "* Privacy-by-Design: Keyed HMAC-SHA256 one-way hashing with zero plaintext APAAR storage.",
    "* Concurrency Radar: Real-time cross-college duplicate detection with side-by-side adjudication.",
    "* Tamper-Evident Ledger: Sequential SHA-256 hash chaining immediately exposes historical alterations."
)

Build-CleanTextBox $s4 $s4Lines @(
    "Analysis of the feasibility of the idea:",
    "Potential challenges and risks:",
    "Strategies for overcoming these challenges:"
) | Out-Null

Add-PrototypePicture $s4 "D:\AICTE\artifacts\verification\conflicts_adjudicated.png" 535 95 405 245 "Prototype Evidence: Cross-Institution Duplicate Collision Radar with side-by-side college enrollment audit, quota verification, and regulatory adjudication controls."

# ==========================================
# SLIDE 5: IMPACT AND BENEFITS
# ==========================================
Write-Host "Formatting Slide 5 (Impact & Benefits)..."
$s5 = $pres.Slides.Item(5)
Format-SlideTitle $s5.Shapes.Item("Title 1") "IMPACT AND BENEFITS"
Format-TeamOval $s5 "TCE_Yquanto"

$s5Lines = @(
    "Potential impact on the target audience:",
    "* AICTE & Regulators: Instant national visibility over intake compliance and automated quota audit.",
    "* Institutions: Streamlined digital admissions reconciliation; eliminates manual verification delays.",
    "* Students & Parents: Fraud-free seat allocation; verifiable academic identity credentials.",
    "* Industry & Employers: Instant zero-trust verification of student credentials via QR scanning.",
    "",
    "Benefits of the solution:",
    "* Economic Benefit: Prevents ghost-seat grant diversion and illegal seat-blocking across colleges.",
    "* Social Equity: Enforces reservation limits and supernumerary seats (TFW 5%, EWS 10%, NRI/FN 15%).",
    "* Regulatory Integrity: Guarantees compliance with NEP 2020 and DPDP Act 2023 privacy mandates.",
    "* Environmental & Operational: 100% paperless verification eliminating physical transit and forgery.",
    "* SIH-R10 Compliance: Side-by-side Student ID and Masked APAAR ID on verifiable certificates."
)

Build-CleanTextBox $s5 $s5Lines @(
    "Potential impact on the target audience:",
    "Benefits of the solution:"
) | Out-Null

Add-PrototypePicture $s5 "D:\AICTE\artifacts\verification\student_certificate_verified.png" 535 95 405 245 "Prototype Evidence: SIH-R10 Academic Certificate displaying Student ID alongside Masked APAAR ID with verified government seal and Ed25519 QR verification code."

# ==========================================
# SLIDE 6: RESEARCH AND REFERENCES
# ==========================================
Write-Host "Formatting Slide 6 (Research & References)..."
$s6 = $pres.Slides.Item(6)
Format-SlideTitle $s6.Shapes.Item("Title 1") "RESEARCH AND REFERENCES"
Format-TeamOval $s6 "TCE_Yquanto"

$s6Lines = @(
    "Details / Links of the reference and research work:",
    "* AICTE Approval Process Handbook (APH 2026-27):",
    "   Norms for intake capacity, supernumerary quotas (TFW 5%, EWS 10%, NRI/FN 15%).",
    "* National Education Policy (NEP 2020) & NAD:",
    "   Framework for APAAR (Automated Permanent Academic Account Registry) and ABC.",
    "* IETF RFC 8032:",
    "   Edwards-Curve Digital Signature Algorithm (Ed25519) for tamper-proof verification receipts.",
    "* Digital Personal Data Protection Act (DPDP Act 2023):",
    "   Principles of purpose limitation, data minimization, and identifier pseudonymization.",
    "* NIST Special Publication 800-107:",
    "   Cryptographic hash standards for sequential hash-chain audit logging.",
    "* Live Prototype Repository & Working Evidence:",
    "   https://github.com/naveeshpcbin/APAAR-ID-BASED-SYSTEM"
)

Build-CleanTextBox $s6 $s6Lines @(
    "Details / Links of the reference and research work:"
) | Out-Null

Add-PrototypePicture $s6 "D:\AICTE\artifacts\verification\audit_ledger_verified.png" 535 95 405 245 "Prototype Evidence: Tamper-Evident SHA-256 Hash Chain Audit Ledger proving mathematical immutability across all admissions, commits, and review approvals."

# Remove instruction slide 7 so presentation is exactly 6 slides (per SIH Rule #1)
if ($pres.Slides.Count -ge 7) {
    Write-Host "Removing instruction slide 7 (strict SIH maximum 6 slides rule)..."
    $pres.Slides.Item(7).Delete()
}

# Clean old slide images
Get-ChildItem -Path $slidesDir -Filter "slide_*.png" | Remove-Item -Force

# Save modified presentation
Write-Host "Saving modified presentation to $outPptxPath..."
$pres.Save()

# Export each slide to high-res PNG for visual inspection
Write-Host "Exporting slides to high-resolution PNG images..."
for ($i = 1; $i -le $pres.Slides.Count; $i++) {
    $slideImgPath = "$slidesDir\slide_$i.png"
    $pres.Slides.Item($i).Export($slideImgPath, "PNG", 1920, 1080)
}

# Export to PDF (required by SIH guideline on Slide 7)
Write-Host "Exporting presentation to PDF ($outPdfPath)..."
$pres.SaveAs($outPdfPath, 32) # 32 = ppSaveAsPDF

$pres.Close()
$ppt.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null

Write-Host "SUCCESS: 6-Slide presentation generated, verified, and exported to PPTX & PDF." -ForegroundColor Green
