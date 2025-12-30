# Quick Setup and Run Script for Windows PowerShell
# 自动激活 venv 并运行脚本

param(
    [string]$Script = "simple_memory.py"
)

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "  LLM Memory System - Quick Launcher" -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host ""

# 检查 venv 是否存在
if (-not (Test-Path "venv")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    
    # 尝试找到 Python
    $python = Get-Command python3.14 -ErrorAction SilentlyContinue
    if (-not $python) {
        $python = Get-Command python -ErrorAction SilentlyContinue
    }
    
    if (-not $python) {
        Write-Host "❌ Python not found! Please install Python first." -ForegroundColor Red
        exit 1
    }
    
    & $python.Source -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

# 激活 venv
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# 检查依赖
Write-Host "📦 Checking dependencies..." -ForegroundColor Yellow
$hasPydantic = python -c "import pydantic" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Dependencies not installed" -ForegroundColor Yellow
    Write-Host "Installing requirements..." -ForegroundColor Yellow
    
    if (Test-Path "requirements.txt") {
        pip install -q -r requirements.txt
    } else {
        pip install -q pydantic pydantic-ai
    }
    
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
}

# 检查 API Key
Write-Host "🔑 Checking API Key..." -ForegroundColor Yellow
if (-not $env:OPENAI_API_KEY) {
    Write-Host "⚠️  OPENAI_API_KEY not set" -ForegroundColor Yellow
    Write-Host "Set it with: `$env:OPENAI_API_KEY = 'sk-...'" -ForegroundColor Cyan
    Write-Host "Continuing without API key (some demos will run in mock mode)..." -ForegroundColor Yellow
} else {
    Write-Host "✓ API Key configured" -ForegroundColor Green
}

Write-Host ""
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "  Running: $Script" -ForegroundColor Green
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host ""

# 运行脚本（支持 demos/ 目录）
if (Test-Path "demos\$Script") {
    python "demos\$Script"
} else {
    python $Script
}

Write-Host ""
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "  Done! Environment still active." -ForegroundColor Green
Write-Host "  Type 'deactivate' to exit venv" -ForegroundColor Yellow
Write-Host "==============================================================================" -ForegroundColor Cyan
