# ImageMagick helper to generate app.ico from app.svg
# Run from the project root: .\scripts\make-icon.ps1

$rootDir = Split-Path -Parent $PSScriptRoot
$INPUT = Join-Path $rootDir "icons\app.svg"
$OUTPUT = Join-Path $rootDir "icons\app.ico"

Write-Host "Converting $INPUT to $OUTPUT..." -ForegroundColor Cyan

magick `
  -background none `
  "$INPUT" `
  -define icon:auto-resize=256,128,64,48,32,24,16 `
  -define icon:format=png `
  -colorspace sRGB `
  "$OUTPUT"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Icon created successfully: $OUTPUT" -ForegroundColor Green
} else {
    Write-Host "Failed to create icon. Make sure ImageMagick is installed and in your PATH." -ForegroundColor Red
    exit 1
}
