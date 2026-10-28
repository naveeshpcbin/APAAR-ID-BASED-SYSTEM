$pptxPath = "D:\AICTE\deck\final\PRAMAAN-AICTE_SIH2026_Final.pptx"
$pdfPath = "D:\AICTE\deck\final\PRAMAAN-AICTE_SIH2026_Final.pdf"
$slidesDir = "D:\AICTE\deck\final\slides"

if (!(Test-Path $slidesDir)) {
    New-Item -ItemType Directory -Path $slidesDir | Out-Null
}

Get-Process -Name "POWERPNT" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 500

$ppt = New-Object -ComObject PowerPoint.Application
$pres = $ppt.Presentations.Open($pptxPath, 0, 0, 0)

Write-Host "Total slides in presentation: " $pres.Slides.Count

# Export high-res PNG of each slide (1920x1080)
for ($i = 1; $i -le $pres.Slides.Count; $i++) {
    $img = "$slidesDir\slide_$i.png"
    $pres.Slides.Item($i).Export($img, "PNG", 1920, 1080)
    Write-Host "Exported slide $i -> $img"
}

# Export PDF
Write-Host "Exporting PDF to $pdfPath..."
$pres.SaveAs($pdfPath, 32)

$pres.Close()
$ppt.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null

Write-Host "PDF & SLIDE PREVIEWS SUCCESSFULLY GENERATED!"

