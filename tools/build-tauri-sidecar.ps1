[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$DistPath = Join-Path $Root "src-tauri\binaries"
$WorkPath = Join-Path $Root "build\tauri-sidecar"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Python virtualenv tidak ditemukan: $Python"
}

New-Item -ItemType Directory -Force -Path $DistPath | Out-Null
New-Item -ItemType Directory -Force -Path $WorkPath | Out-Null

Push-Location $Root
try {
    & $Python -m PyInstaller `
        --noconfirm `
        --clean `
        --onefile `
        --windowed `
        --name "lancar-api-x86_64-pc-windows-msvc" `
        --distpath $DistPath `
        --workpath $WorkPath `
        --specpath $WorkPath `
        --add-data "$Root\api\templates;api/templates" `
        --add-data "$Root\api\static;api/static" `
        --copy-metadata fastapi `
        --copy-metadata starlette `
        --copy-metadata pydantic `
        --copy-metadata uvicorn `
        --exclude-module PySide6 `
        --exclude-module legacy_ui `
        --hidden-import uvicorn.logging `
        --hidden-import uvicorn.loops `
        --hidden-import uvicorn.loops.auto `
        --hidden-import uvicorn.protocols `
        --hidden-import uvicorn.protocols.http `
        --hidden-import uvicorn.protocols.http.auto `
        --hidden-import uvicorn.protocols.websockets `
        --hidden-import uvicorn.protocols.websockets.auto `
        --hidden-import uvicorn.lifespan `
        --hidden-import uvicorn.lifespan.on `
        --hidden-import uvicorn.lifespan.off `
        --hidden-import sqlalchemy.sql.default_comparator `
        sidecar_main.py

    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller sidecar build gagal dengan exit code $LASTEXITCODE."
    }
} finally {
    Pop-Location
}

Write-Host "Sidecar siap: $(Join-Path $DistPath 'lancar-api-x86_64-pc-windows-msvc.exe')"
