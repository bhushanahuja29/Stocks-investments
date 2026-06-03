# Krypto launcher — set backend URL then start desktop app
$env:JARVIS_BACKEND_URL = "http://192.168.29.31:8000"

Set-Location $PSScriptRoot
.\.venv\Scripts\Activate.ps1
python run_jarvis.py
