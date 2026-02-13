$ErrorActionPreference = "Stop"

Write-Host "[check] Backend tests"
Push-Location backend
python -m pytest -q
Pop-Location

Write-Host "[check] Frontend lint + typecheck + test + build"
Push-Location frontend
npm run check
Pop-Location

Write-Host "[check] OK"
