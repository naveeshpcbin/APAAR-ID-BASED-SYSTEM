$pptxPath = "D:\AICTE\finaldemoppt\PRAMAAN_AICTE_SIH2026_INTERACTIVE_WINNING.pptx"
$pdfPath  = "D:\AICTE\finaldemoppt\PRAMAAN_AICTE_SIH2026_INTERACTIVE_WINNING.pdf"
$slidesDir = "D:\AICTE\finaldemoppt\slides_interactive"

if (!(Test-Path $slidesDir)) {
    New-Item -ItemType Directory -Path $slidesDir -Force | Out-Null
}

Get-Process -Name "POWERPNT" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 500

$ppt = New-Object -ComObject PowerPoint.Application

Write-Host "Opening interactive winning presentation: $pptxPath"
$pres = $ppt.Presentations.Open($pptxPath, 0, 0, 0)
Write-Host "Total slides in presentation: " $pres.Slides.Count

for ($i = 1; $i -le $pres.Slides.Count; $i++) {
    $img = "$slidesDir\slide_$i.png"
    $pres.Slides.Item($i).Export($img, "PNG", 1920, 1080)
    Write-Host "Exported slide $i -> $img"
}

Write-Host "Exporting PDF to $pdfPath..."
$pres.SaveAs($pdfPath, 32)
$pres.Close()

$ppt.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
Write-Host "INTERACTIVE WINNING PRESENTATION EXPORT COMPLETE!"
