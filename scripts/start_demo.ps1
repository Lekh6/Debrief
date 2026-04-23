$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$backendDir = Join-Path $repoRoot "backend"
$frontendDir = Join-Path $repoRoot "frontend"
$pythonPath = Join-Path $repoRoot ".venv\\Scripts\\python.exe"

if (-not (Test-Path $pythonPath)) {
    Write-Error "Missing Python venv at '$pythonPath'. Create it first or update this script."
}

$backendCommand = "Set-Location '$backendDir'; & '$pythonPath' -m uvicorn app.main:app --host 127.0.0.1 --port 8005"
$frontendCommand = "Set-Location '$frontendDir'; npm run dev"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand | Out-Null
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand | Out-Null

Write-Host ""
Write-Host "Demo services started in separate terminals:"
Write-Host "Backend:  http://127.0.0.1:8005"
Write-Host "Frontend: http://localhost:5173"
Write-Host ""
Write-Host "Use host login: leka / le124"
