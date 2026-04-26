Push-Location -Path $PSScriptRoot
try {
    & .\.venv\Scripts\Activate.ps1
    python server.py
}
finally {
    Pop-Location
}
