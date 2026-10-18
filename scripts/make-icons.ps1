Add-Type -AssemblyName System.Drawing
$iconFolder = Join-Path $PSScriptRoot '../public/icons'
New-Item -ItemType Directory -Force -Path $iconFolder | Out-Null
foreach ($size in @(192, 512)) {
  $bitmap = New-Object System.Drawing.Bitmap($size, $size)
  $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
  $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
  $graphics.Clear([System.Drawing.ColorTranslator]::FromHtml('#0b1220'))
  $pen = New-Object System.Drawing.Pen([System.Drawing.ColorTranslator]::FromHtml('#65e2c3'), ($size * 0.035))
  $pen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
  $pen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
  $coords = @(@(.23,.52), @(.37,.52), @(.44,.32), @(.56,.68), @(.64,.46), @(.77,.46))
  $points = $coords | ForEach-Object { New-Object System.Drawing.PointF(($size * $_[0]), ($size * $_[1])) }
  $graphics.DrawLines($pen, [System.Drawing.PointF[]]$points)
  $bitmap.Save((Join-Path $iconFolder "icon-$size.png"), [System.Drawing.Imaging.ImageFormat]::Png)
  if ($size -eq 512) { $bitmap.Save((Join-Path $iconFolder 'maskable-512.png'), [System.Drawing.Imaging.ImageFormat]::Png) }
  $pen.Dispose(); $graphics.Dispose(); $bitmap.Dispose()
}
