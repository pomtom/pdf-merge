# PDF Studio launcher: bootstraps a virtual environment, installs
# dependencies, opens the browser and starts the server.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv venv .venv --python 3.12
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        py -3 -m venv .venv
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        python -m venv .venv
    } else {
        Write-Error "No Python found. Install Python 3.11+ or uv (https://docs.astral.sh/uv/)."
    }
}

# Install dependencies if FastAPI is missing from the venv
& $venvPython -c "import fastapi" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing dependencies..." -ForegroundColor Cyan
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv pip install -r requirements.txt --python $venvPython
    } else {
        & $venvPython -m pip install -r requirements.txt
    }
}

$url = "http://127.0.0.1:8000"
Write-Host "Starting PDF Studio at $url" -ForegroundColor Green
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 2
    Start-Process $using:url
} | Out-Null

& $venvPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000
