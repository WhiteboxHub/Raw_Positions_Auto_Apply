# Raw_Positions_Auto_Apply Daily Scheduler Wrapper (Dynamic Web Mode)
# This script is intended to be run by Windows Task Scheduler

$ProjectRoot = "C:\Users\remot\Documents\Raw_Positions_Auto_Apply"
$VenvPython = "$ProjectRoot\venv\Scripts\python.exe"

# Change to project directory
Set-Location $ProjectRoot

# 1. Refresh Whitebox API Tokens (handles expired sessions)
Write-Host "Refreshing login tokens..."
& $VenvPython auto_login.py

# 2. Run the application in Web Mode
# Automatically fetches latest jobs and runs for candidates enabled on the marketing page
Write-Host "Running Raw Positions Pipeline in Web Mode..."
& $VenvPython run.py --fetch --run-all

# Optional: Log execution to a file
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path "$ProjectRoot\logs\scheduler.log" -Value "[$Timestamp] Dynamic Web Run completed."
