$ppt = New-Object -ComObject PowerPoint.Application
$pres = $ppt.Presentations.Open("d:\AICTE\demoppt\SIH2026-IDEA-Presentation-Format (1).pptx", 1, 0, 0)

$slide1 = $pres.Slides.Item(1)
$tb = $slide1.Shapes.Item("TextBox 9")
Write-Host "TextBox 9 Font: $($tb.TextFrame.TextRange.Font.Name), Size: $($tb.TextFrame.TextRange.Font.Size)"

$slide2 = $pres.Slides.Item(2)
$t2 = $slide2.Shapes.Item("Title 1")
Write-Host "Slide 2 Title Font: $($t2.TextFrame.TextRange.Font.Name), Size: $($t2.TextFrame.TextRange.Font.Size)"

$b2 = $slide2.Shapes.Item("TextBox 8")
Write-Host "Slide 2 Body Font: $($b2.TextFrame.TextRange.Font.Name), Size: $($b2.TextFrame.TextRange.Font.Size)"

$pres.Close()
$ppt.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
