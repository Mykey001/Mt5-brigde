# MT5 Bridge API - Windows Deployment Script
# This script sets up and runs the MT5 Bridge API on Windows

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MT5 Bridge API - Windows Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check Python
Write-Host "`nChecking Python installation..." -ForegroundColor Yellow
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "ERROR: Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}
Write-Host "Python found: $($python.Source)" -ForegroundColor Green

# Check MT5 Terminal
Write-Host "`nChecking MT5 Terminal..." -ForegroundColor Yellow
$mt5Path = "C:\Program Files\MetaTrader 5\terminal64.exe"
if (-not (Test-Path $mt5Path)) {
    Write-Host "WARNING: MT5 Terminal not found at default path" -ForegroundColor Yellow
    Write-Host "Please ensure MT5 is installed and update MT5_PATH in app/mt5/manager.py" -ForegroundColor Yellow
} else {
    Write-Host "MT5 Terminal found: $mt5Path" -ForegroundColor Green
}

# Install dependencies
Write-Host "`nInstalling Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "Dependencies installed successfully" -ForegroundColor Green

# Check .env file
Write-Host "`nChecking configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "Please edit .env with your configuration" -ForegroundColor Yellow
}

# Start Docker services (if Docker is available)
Write-Host "`nChecking Docker for database services..." -ForegroundColor Yellow
$docker = Get-Command docker -ErrorAction SilentlyContinue
if ($docker) {
    Write-Host "Starting PostgreSQL and Redis via Docker..." -ForegroundColor Yellow
    docker-compose up -d postgres redis
    Start-Sleep -Seconds 5
    Write-Host "Database services started" -ForegroundColor Green
} else {
    Write-Host "Docker not found. Please ensure PostgreSQL and Redis are running." -ForegroundColor Yellow
}

# Start the API
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Starting MT5 Bridge API..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Green
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
