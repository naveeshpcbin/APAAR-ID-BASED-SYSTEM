$ppt = New-Object -ComObject PowerPoint.Application
$pres = $ppt.Presentations.Open("d:\AICTE\demoppt\SIH2026-IDEA-Presentation-Format (1).pptx", 1, 0, 0)
Write-Host "Total Slides in template: $($pres.Slides.Count)"
$pres.Close()
$ppt.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
