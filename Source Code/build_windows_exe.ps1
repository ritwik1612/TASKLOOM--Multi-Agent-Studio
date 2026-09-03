param(
    [string]$Python = ".\.venv\Scripts\python.exe",
    [switch]$Console
)

$ErrorActionPreference = "Stop"

& $Python -m pip install -r requirements.txt -r requirements-build.txt
$uiMode = if ($Console) { "--console" } else { "--windowed" }

& $Python -m PyInstaller --noconfirm --clean --name "Taskloom" $uiMode `
    --icon "assets\taskloom.ico" `
    --contents-directory "Taskloom Runtime" `
    --collect-all streamlit `
    --collect-all google.genai `
    --collect-all pydantic `
    --collect-all diskcache `
    --collect-all reportlab `
    --collect-all keyring `
    --collect-all webview `
    --add-data "app.py;." `
    --add-data "config.py;." `
    --add-data "credential_store.py;." `
    --add-data "paths.py;." `
    --add-data "orchestrator.py;." `
    --add-data "artifacts.py;." `
    --add-data "schemas.py;." `
    --add-data "agents;agents" `
    --add-data "providers;providers" `
    --add-data "assets;assets" `
    --add-data "FONTS;FONTS" `
    --add-data ".streamlit;.streamlit" `
    desktop_launcher.py

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE."
}

Write-Host "Built executable: dist\Taskloom\Taskloom.exe"
