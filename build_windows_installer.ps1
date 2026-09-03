param(
    [string]$Python = ".\.venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\dist\Taskloom\Taskloom.exe")) {
    Write-Host "Desktop app build not found; building Taskloom first..."
    & .\build_windows_exe.ps1 -Python $Python
}

& $Python -m PyInstaller --noconfirm --clean --onefile --windowed `
    --name "Taskloom Setup" `
    --icon "assets\taskloom.ico" `
    --add-data "dist\Taskloom;TaskloomPayload" `
    desktop_installer.py

if ($LASTEXITCODE -ne 0) {
    throw "Installer build failed with exit code $LASTEXITCODE."
}

$release = Join-Path $PSScriptRoot "Taskloom Installer"
New-Item -ItemType Directory -Force -Path $release | Out-Null
Copy-Item -LiteralPath ".\dist\Taskloom Setup.exe" -Destination (Join-Path $release "Taskloom Setup.exe") -Force

@"
TASKLOOM DESKTOP INSTALLER

1. Double-click Taskloom Setup.exe.
2. Approve Windows' administrator prompt. This is needed only because the default install location is Program Files.
3. Keep the default location or click Browse to choose another folder.
4. Open Taskloom after installation.

On first use, select Connect Gemini to create and securely save your personal Gemini API key(s).
"@ | Set-Content -LiteralPath (Join-Path $release "START HERE.txt") -Encoding utf8

Write-Host "Installer ready: Taskloom Installer\Taskloom Setup.exe"
