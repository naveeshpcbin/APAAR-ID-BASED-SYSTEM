# PRAMAAN-AICTE — One-Click Demonstration Launcher
# Usage in PowerShell: .\opendemo  OR  opendemo

$ErrorActionPreference = "SilentlyContinue"

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "   PRAMAAN-AICTE -- Smart India Hackathon 2026 (SIH26263)       " -ForegroundColor Yellow
Write-Host "   Dual Portal Admission Reconciliation & Verification Engine   " -ForegroundColor Cyan
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
    $res = Invoke-WebRequest -Uri "http://localhost:3000/login" -UseBasicParsing -TimeoutSec 2
    if ($res.StatusCode -eq 200) { $frontendHealthy = $true }
} catch { $frontendHealthy = $false }

if ($frontendHealthy) {
    Write-Host "[ALREADY RUNNING]" -ForegroundColor Green
} else {
    Write-Host "[STARTING]" -ForegroundColor Yellow
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run dev" -WorkingDirectory "$baseDir\frontend" -WindowStyle Minimized
    Start-Sleep -Seconds 4
}

# 3. Launch ONLY the Authentication Portal Entry Page in Default Browser
Write-Host "[3/3] Opening PRAMAAN-AICTE Authentication Portal in Default Browser..." -ForegroundColor Cyan

# Open ONLY http://localhost:3000/login so user can manually choose and enter credentials
try {
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c start `"`" `"http://localhost:3000/login`"" -WindowStyle Hidden
} catch {
    Start-Process "http://localhost:3000/login"
}

Write-Host ""
Write-Host "SUCCESS: PRAMAAN-AICTE Authentication Portal opened in your browser!" -ForegroundColor Green
Write-Host ""
Write-Host "-----------------------------------------------------------------" -ForegroundColor Gray
Write-Host " AUTHENTICATION ENTRY POINT:" -ForegroundColor White
Write-Host "   -> http://localhost:3000/login" -ForegroundColor Cyan
Write-Host "-----------------------------------------------------------------" -ForegroundColor Gray
Write-Host ""
Write-Host " DEMO TEST CREDENTIALS (Choose your role):" -ForegroundColor Yellow
Write-Host "   1. College Portal (DTU Delhi)    : nodal.dtu@dtu.ac.in      | Pass: College@12345" -ForegroundColor White
Write-Host "   2. College Portal (COEP Pune)    : nodal.coep@coep.ac.in    | Pass: College@12345" -ForegroundColor White
Write-Host "   3. AICTE Central HQ (Advisor-I)  : aicte.admin@pramaan.gov.in | Pass: Admin@12345" -ForegroundColor White
Write-Host "   4. AICTE Regional Office (WRO)   : ro.mumbai@aicte.gov.in   | Pass: Officer@12345" -ForegroundColor White
Write-Host ""
Write-Host " Tip: Single-click autofill buttons are also available on both login pages for fast testing." -ForegroundColor Yellow
Write-Host ""
