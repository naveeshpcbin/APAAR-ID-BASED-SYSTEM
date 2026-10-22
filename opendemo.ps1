# PRAMAAN-AICTE — One-Click Demonstration Launcher
# Usage in PowerShell: .\opendemo  OR  opendemo

$ErrorActionPreference = "SilentlyContinue"

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "   PRAMAAN-AICTE -- Smart India Hackathon 2026 (SIH26263)       " -ForegroundColor Yellow
Write-Host "   Automated Demo Launcher and Multi-Workspace Orchestrator     " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

$baseDir = "D:\AICTE"

# 1. Check and Start Backend if not already running
Write-Host "[1/3] Checking FastAPI Backend (Port 8000)... " -NoNewline
$backendHealthy = $false
try {
    $res = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" -Method Get -TimeoutSec 2
    if ($res.status -eq "UP") { $backendHealthy = $true }
} catch { $backendHealthy = $false }

if ($backendHealthy) {
    Write-Host "[ALREADY RUNNING]" -ForegroundColor Green
} else {
    Write-Host "[STARTING]" -ForegroundColor Yellow
    $pyExe = "$baseDir\backend\venv\Scripts\python.exe"
    Start-Process -FilePath $pyExe -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir $baseDir\backend" -WorkingDirectory "$baseDir\backend" -WindowStyle Minimized
    Start-Sleep -Seconds 3
}

# 2. Check and Start Frontend if not already running
Write-Host "[2/3] Checking Next.js Frontend (Port 3000)... " -NoNewline
$frontendHealthy = $false
try {
    $res = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 2
    if ($res.StatusCode -eq 200) { $frontendHealthy = $true }
} catch { $frontendHealthy = $false }

if ($frontendHealthy) {
    Write-Host "[ALREADY RUNNING]" -ForegroundColor Green
} else {
    Write-Host "[STARTING]" -ForegroundColor Yellow
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run start" -WorkingDirectory "$baseDir\frontend" -WindowStyle Minimized
    Start-Sleep -Seconds 4
}

# 3. Launch All Demonstration Pages in Default Browser
Write-Host "[3/3] Opening PRAMAAN-AICTE Workspaces in Default Browser..." -ForegroundColor Cyan

$urls = @(
    "http://localhost:3000/dashboard",
    "http://localhost:3000/uploads",
    "http://localhost:3000/admissions",
    "http://localhost:3000/conflicts",
    "http://localhost:3000/anomalies",
    "http://localhost:3000/verification",
    "http://localhost:3000/audit",
    "http://127.0.0.1:8000/docs"
)

foreach ($u in $urls) {
    Start-Process $u
    Start-Sleep -Milliseconds 400
}

Write-Host ""
Write-Host "SUCCESS: All 8 demonstration workspaces opened in your browser!" -ForegroundColor Green
Write-Host ""
Write-Host "-----------------------------------------------------------------" -ForegroundColor Gray
Write-Host " Opened Workspaces:" -ForegroundColor White
Write-Host "   1. Central and Institutional Dashboard : http://localhost:3000/dashboard" -ForegroundColor Gray
Write-Host "   2. Smart Ingestion and Batch Review    : http://localhost:3000/uploads" -ForegroundColor Gray
Write-Host "   3. Student Admissions and Certificates : http://localhost:3000/admissions" -ForegroundColor Gray
Write-Host "   4. Cross-Institution Conflict Radar    : http://localhost:3000/conflicts" -ForegroundColor Gray
Write-Host "   5. Explainable Regulatory Anomalies    : http://localhost:3000/anomalies" -ForegroundColor Gray
Write-Host "   6. QR Receipt Ed25519 Verification     : http://localhost:3000/verification" -ForegroundColor Gray
Write-Host "   7. Tamper-Evident SHA-256 Ledger       : http://localhost:3000/audit" -ForegroundColor Gray
Write-Host "   8. Interactive OpenAPI Documentation   : http://127.0.0.1:8000/docs" -ForegroundColor Gray
Write-Host "-----------------------------------------------------------------" -ForegroundColor Gray
Write-Host ""
Write-Host " Quick Demo Role Switcher is available in the top-right header on all pages." -ForegroundColor Yellow
Write-Host ""
