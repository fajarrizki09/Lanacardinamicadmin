[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$SourceGateway = Join-Path $Root "openwa_server"
$SourceNode = Join-Path $Root "tools\node"
$RuntimeRoot = Join-Path $Root "src-tauri\runtime"
$TargetGateway = Join-Path $RuntimeRoot "openwa_server"
$TargetNode = Join-Path $RuntimeRoot "node"

function Assert-WithinWorkspace([string] $Path) {
    $workspace = [System.IO.Path]::GetFullPath($Root).TrimEnd('\') + '\'
    $resolved = [System.IO.Path]::GetFullPath($Path)
    if (-not $resolved.StartsWith($workspace, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path staging di luar workspace ditolak: $resolved"
    }
}

if (-not (Test-Path -LiteralPath (Join-Path $SourceGateway "server.js"))) {
    throw "Source WhatsApp gateway tidak ditemukan di $SourceGateway"
}
if (-not (Test-Path -LiteralPath (Join-Path $SourceGateway "node_modules"))) {
    throw "Dependency WhatsApp gateway belum tersedia. Jalankan npm install di openwa_server terlebih dahulu."
}
if (-not (Test-Path -LiteralPath (Join-Path $SourceNode "node.exe"))) {
    throw "Runtime Node portable tidak ditemukan di tools\node."
}

Assert-WithinWorkspace $RuntimeRoot
if (Test-Path -LiteralPath $RuntimeRoot) {
    Remove-Item -LiteralPath $RuntimeRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $TargetGateway, $TargetNode | Out-Null

$gatewayExit = & robocopy $SourceGateway $TargetGateway /E /XD data .node-persist .wwebjs_auth .wwebjs_cache sessions logs .cache cache tmp /XF *.log *.tmp *.bak server.new*.js
if ($LASTEXITCODE -ge 8) {
    throw "Staging openwa_server gagal (robocopy exit $LASTEXITCODE).`n$gatewayExit"
}

$nodeExit = & robocopy $SourceNode $TargetNode /E /XD .cache cache logs tmp /XF *.log *.tmp *.bak
if ($LASTEXITCODE -ge 8) {
    throw "Staging Node runtime gagal (robocopy exit $LASTEXITCODE).`n$nodeExit"
}

$forbidden = @(
    (Join-Path $TargetGateway "data"),
    (Join-Path $TargetGateway ".node-persist"),
    (Join-Path $TargetGateway ".wwebjs_auth"),
    (Join-Path $TargetGateway ".wwebjs_cache"),
    (Join-Path $TargetGateway "sessions"),
    (Join-Path $TargetGateway "logs"),
    (Join-Path $TargetGateway ".cache")
)
foreach ($path in $forbidden) {
    if (Test-Path -LiteralPath $path) {
        throw "Runtime data terlarang ikut staging: $path"
    }
}

Write-Host "Runtime Tauri staged tanpa session/cache gateway: $RuntimeRoot"
