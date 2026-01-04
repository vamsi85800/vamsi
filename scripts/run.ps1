# Helper: create venv, install deps, and run server using venv python (no activation required)
# Usage: Right-click -> Run with PowerShell or run from PowerShell:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force; .\scripts\run.ps1

$projectRoot = (Resolve-Path "$PSScriptRoot\..\").Path
$venvPath = Join-Path $projectRoot ".venv"
$py = Join-Path $venvPath "Scripts\python.exe"

if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment at $venvPath..."
    python -m venv $venvPath
}

if (-not (Test-Path $py)) {
    Write-Error "Python venv not found at $py. Ensure Python is installed and on PATH."
    exit 1
}

Write-Host "Installing dependencies..."
& $py -m pip install --upgrade pip
& $py -m pip install -r (Join-Path $projectRoot "requirements.txt")
& $py -m pip install -e $projectRoot

Write-Host "Starting server (uvicorn)..."
& $py -m uvicorn genai_project.api:app --reload --port 8000
