$targets = @(
    @{
        pptx = "D:\AICTE\finaldemoppt\PRAMAAN_AICTE_SIH2026_FINAL.pptx"
        pdf  = "D:\AICTE\finaldemoppt\PRAMAAN_AICTE_SIH2026_FINAL.pdf"
        dir  = "D:\AICTE\finaldemoppt\slides"
    },
    @{
        pptx = "D:\AICTE\deck\final\PRAMAAN-AICTE_SIH2026_Final.pptx"
        pdf  = "D:\AICTE\deck\final\PRAMAAN-AICTE_SIH2026_Final.pdf"
        dir  = "D:\AICTE\deck\final\slides"
    }
)

Get-Process -Name "POWERPNT" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 500

$ppt = New-Object -ComObject PowerPoint.Application

foreach ($target in $targets) {
    $pptxPath = $target.pptx
    $pdfPath = $target.pdf
    $slidesDir = $target.dir

    if (!(Test-Path $slidesDir)) {
        New-Item -ItemType Directory -Path $slidesDir -Force | Out-Null
    }

    Write-Host "Opening presentation: $pptxPath"
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
}

$ppt.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
Write-Host "ALL DELIVERABLES SUCCESSFULLY EXPORTED AS VECTOR PDF & 1080p PNGs!"
