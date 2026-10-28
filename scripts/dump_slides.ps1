$ppt = New-Object -ComObject PowerPoint.Application
$pres = $ppt.Presentations.Open("d:\AICTE\demoppt\SIH2026-IDEA-Presentation-Format (1).pptx", 1, 0, 0)

for ($i = 1; $i -le $pres.Slides.Count; $i++) {
    $slide = $pres.Slides.Item($i)
    Write-Host "=== SLIDE $i ===" -ForegroundColor Cyan
    for ($j = 1; $j -le $slide.Shapes.Count; $j++) {
        $shape = $slide.Shapes.Item($j)
        $hasText = $shape.HasTextFrame
        $txt = ""
        if ($hasText -and $shape.TextFrame.HasText) {
            $txt = $shape.TextFrame.TextRange.Text.Replace("`r", " | ").Replace("`n", " | ")
        }
        Write-Host "  Shape $j [Name: $($shape.Name), Type: $($shape.Type), L: $([int]$shape.Left), T: $([int]$shape.Top), W: $([int]$shape.Width), H: $([int]$shape.Height)] Text: $txt"
    }
}

$pres.Close()
$ppt.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
