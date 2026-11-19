[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("pre-install", "post-install", "before-close", "after-close", "pre-upgrade", "post-upgrade")]
    [string] $Stage,

    [Parameter(Mandatory = $true)]
    [string] $InstallerPath,

    [string] $OutputDir = (Join-Path $env:TEMP "LancarDynamicAdmin-Phase3B"),

    [string] $LegacyInstallerPath = "",

    [string] $InstallPath = "",

    [string] $AppDataPath = (Join-Path $env:APPDATA "LancarDinamicAdmin")
)

$ErrorActionPreference = "Stop"
$ExpectedSha256 = "5E40E6A0B6C79D3B70AEBE9E093934884CD91794F1C3DFC637A4BC3CC8CC1A8E"

function Get-FileEvidence([string] $Path) {
    if (-not $Path -or -not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $null
    }
    $item = Get-Item -LiteralPath $Path
    return [ordered]@{
        path = $item.FullName
        bytes = $item.Length
        mib = [math]::Round($item.Length / 1MB, 2)
        sha256 = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash
        last_write_time = $item.LastWriteTime.ToString("o")
    }
}

function Get-FolderBytes([string] $Path) {
    if (-not $Path -or -not (Test-Path -LiteralPath $Path -PathType Container)) {
        return $null
    }
    $bytes = (Get-ChildItem -LiteralPath $Path -File -Recurse -Force -ErrorAction SilentlyContinue |
        Measure-Object -Property Length -Sum).Sum
    if ($null -eq $bytes) {
        $bytes = 0
    }
    return [ordered]@{
        path = (Resolve-Path -LiteralPath $Path).Path
        bytes = [int64]$bytes
        mib = [math]::Round($bytes / 1MB, 2)
    }
}

function Get-LargestChildren([string] $Path) {
    if (-not $Path -or -not (Test-Path -LiteralPath $Path -PathType Container)) {
        return @()
    }
    return @(
        Get-ChildItem -LiteralPath $Path -Directory -Force -ErrorAction SilentlyContinue |
            ForEach-Object { Get-FolderBytes $_.FullName } |
            Sort-Object -Property bytes -Descending |
            Select-Object -First 10
    )
}

function Get-WebView2Version() {
    $paths = @(
        "HKLM:\SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
        "HKCU:\SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
    )
    foreach ($path in $paths) {
        $value = Get-ItemProperty -LiteralPath $path -ErrorAction SilentlyContinue
        if ($value -and $value.pv) {
            return [ordered]@{ version = $value.pv; registry_path = $path }
        }
    }
    return [ordered]@{ version = $null; registry_path = $null }
}

function Get-OsEvidence() {
    $registry = Get-ItemProperty -LiteralPath "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion" -ErrorAction SilentlyContinue
    return [ordered]@{
        product_name = $registry.ProductName
        display_version = $registry.DisplayVersion
        current_build = $registry.CurrentBuild
        ubr = $registry.UBR
        architecture = $env:PROCESSOR_ARCHITECTURE
        user_profile = $env:USERPROFILE
        username = $env:USERNAME
        computer_name = $env:COMPUTERNAME
    }
}

function Get-ProcessEvidence() {
    return @(
        Get-Process -ErrorAction SilentlyContinue |
            Where-Object { $_.ProcessName -match "lancar|node|python" } |
            ForEach-Object {
                $path = $null
                try { $path = $_.Path } catch {}
                [ordered]@{
                    pid = $_.Id
                    name = $_.ProcessName
                    path = $path
                    relevant = ($_.ProcessName -match "lancar|node")
                }
            }
    )
}

function Get-UninstallEvidence() {
    $roots = @(
        "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
    )
    return @(
        foreach ($root in $roots) {
            Get-ItemProperty -Path $root -ErrorAction SilentlyContinue |
                Where-Object { $_.DisplayName -match "Lancar" } |
                Select-Object DisplayName, DisplayVersion, InstallLocation, UninstallString, PSPath
        }
    )
}

function Get-ShortcutEvidence() {
    $roots = @(
        [Environment]::GetFolderPath("Desktop"),
        [Environment]::GetFolderPath("Programs"),
        [Environment]::GetFolderPath("CommonPrograms")
    )
    return @(
        foreach ($root in $roots) {
            if (Test-Path -LiteralPath $root -PathType Container) {
                Get-ChildItem -LiteralPath $root -Filter "*Lancar*.lnk" -File -Recurse -ErrorAction SilentlyContinue |
                    Select-Object -ExpandProperty FullName
            }
        }
    )
}

function Get-FixtureHashes([string] $Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        return @()
    }
    return @(
        Get-ChildItem -LiteralPath $Path -File -Recurse -Force -ErrorAction SilentlyContinue |
            Where-Object {
                $_.FullName -notmatch "(?i)\\whatsapp_gateway\\|\\sessions?\\|\\auth\\|\\cache\\|\\logs\\|\.node-persist"
            } |
            ForEach-Object {
                [ordered]@{
                    relative_path = $_.FullName.Substring($Path.TrimEnd("\").Length).TrimStart("\")
                    bytes = $_.Length
                    sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
                }
            }
    )
}

function Find-InstallPath([string] $ExplicitPath) {
    $candidates = @(
        $ExplicitPath,
        (Join-Path $env:LOCALAPPDATA "Lancar Dynamic Admin"),
        (Join-Path $env:LOCALAPPDATA "Programs\Lancar Dynamic Admin"),
        (Join-Path $env:ProgramFiles "Lancar Dynamic Admin"),
        (Join-Path ${env:ProgramFiles(x86)} "Lancar Dynamic Admin")
    ) | Where-Object { $_ }
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Container) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    return $ExplicitPath
}

$installer = Get-FileEvidence $InstallerPath
if ($null -eq $installer) {
    throw "Installer RC tidak ditemukan: $InstallerPath"
}
if ($installer.sha256 -ne $ExpectedSha256.ToUpperInvariant()) {
    throw "SHA-256 installer tidak sesuai RC Phase 4A-CSP Final. Expected: $ExpectedSha256; Actual: $($installer.sha256)"
}

$resolvedInstallPath = Find-InstallPath $InstallPath
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
$safeStage = $Stage.Replace("-", "_")
$reportPath = Join-Path $OutputDir "$timestamp-$safeStage.json"

$logPaths = @(
    (Join-Path $AppDataPath "logs\desktop_sidecar.log"),
    (Join-Path $AppDataPath "logs\whatsapp_gateway.log"),
    (Join-Path $env:LOCALAPPDATA "com.lancardynamic.admin\logs\desktop_shell.log")
)

$report = [ordered]@{
    phase = "Phase 3D-R3 REOPENED - Phase 4A-CSP Final Installed-App Gateway & UI Regression Validation"
    stage = $Stage
    captured_at = (Get-Date).ToString("o")
    expected_rc_sha256 = $ExpectedSha256.ToUpperInvariant()
    installer = $installer
    legacy_installer = Get-FileEvidence $LegacyInstallerPath
    os = Get-OsEvidence
    webview2 = Get-WebView2Version
    paths = [ordered]@{
        install = $resolvedInstallPath
        app_data = $AppDataPath
        output = (Resolve-Path -LiteralPath $OutputDir).Path
    }
    install_size = Get-FolderBytes $resolvedInstallPath
    app_data_size = Get-FolderBytes $AppDataPath
    largest_install_children = Get-LargestChildren $resolvedInstallPath
    largest_app_data_children = Get-LargestChildren $AppDataPath
    logs = @(
        foreach ($logPath in $logPaths) {
            $entry = Get-FileEvidence $logPath
            if ($entry) { $entry } else { [ordered]@{ path = $logPath; exists = $false } }
        }
    )
    processes = Get-ProcessEvidence
    shortcuts = Get-ShortcutEvidence
    uninstall_entries = Get-UninstallEvidence
    fixture_hashes_without_gateway_state = Get-FixtureHashes $AppDataPath
    manual_checks_required = @(
        "License/login flow membuka dashboard",
        "Tidak ada window CMD muncul",
        "External URL allowlist terbuka dan URL berbahaya ditolak",
        "Open folder, open/print invoice, download/export berhasil",
        "Gateway WhatsApp start/stop dari UI",
        "Loading screen kegagalan sidecar menunjukkan lokasi log",
        "After-close tidak memiliki lancar-api/node/OpenWA residual",
        "Post-upgrade data, lisensi, shortcut, uninstall entry, dan app-data path sesuai"
    )
}

$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $reportPath -Encoding UTF8
Write-Host "Evidence Phase 3D-R3 REOPENED / Phase 4A-CSP Final tersimpan: $reportPath"
Write-Host "Installer SHA-256 tervalidasi: $($installer.sha256)"
