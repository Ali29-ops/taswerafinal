Write-Host "Starting Photo Printing Management System..." -ForegroundColor Cyan
Set-Location $PSScriptRoot\..

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example" -ForegroundColor Yellow
}

docker compose up --build -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Application is running!" -ForegroundColor Green
    Write-Host "  Frontend:  http://localhost"
    Write-Host "  API Docs:  http://localhost/docs"
    Write-Host ""
    Write-Host "Default credentials:"
    Write-Host "  Admin:    admin@system.com / Admin123!"
    Write-Host "  Manager:  manager@system.com / Manager123!"
    Write-Host "  Employee: employee@system.com / Employee123!"
} else {
    Write-Host "Failed to start. Ensure Docker Desktop is running." -ForegroundColor Red
}
