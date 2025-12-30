# Quick Activate Script
# Fast activation for virtual environment

Write-Host "Activating virtual environment..." -ForegroundColor Cyan

if (-not (Test-Path "venv")) {
    Write-Host "Virtual environment not found!" -ForegroundColor Red
    Write-Host "Run: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

& .\venv\Scripts\Activate.ps1

Write-Host "Environment activated successfully" -ForegroundColor Green
Write-Host ""
Write-Host "Available commands:" -ForegroundColor Cyan
Write-Host "  python simple_memory.py       - Run minimal demo" -ForegroundColor White
Write-Host "  python pydantic_ai_demo.py    - Run full demo" -ForegroundColor White
Write-Host "  python comparison.py          - Show old vs new comparison" -ForegroundColor White
Write-Host "  pytest tests/ -v              - Run tests" -ForegroundColor White
Write-Host "  deactivate                    - Exit environment" -ForegroundColor White
Write-Host ""
