#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Bump version, commit, tag, and push in one command.

.DESCRIPTION
    Runs the Python version bumper, commits version files, creates an annotated tag,
    and pushes both the commit and tag to origin.

.PARAMETER Type
    Version bump type: 'patch' (default), 'minor', 'major'

.PARAMETER Message
    Custom commit message (default: "chore: bump version to X.Y.Z")

.PARAMETER Push
    Whether to push to origin (default: $true)

.PARAMETER Remote
    Git remote name (default: 'origin')

.EXAMPLE
    .\tools\release.ps1                    # patch bump + push
    .\tools\release.ps1 -Type minor       # minor bump + push
    .\tools\release.ps1 -Type major -Push:$false  # major bump, no push
#>

param(
    [ValidateSet('patch','minor','major')]
    [string]$Type = 'patch',

    [string]$Message = '',

    [switch]$Push = $true,

    [string]$Remote = 'origin'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = Split-Path $PSScriptRoot -Parent

# 1. Bump version using Python script (patch only for now)
if ($Type -ne 'patch') {
    Write-Warning "Only 'patch' bump is implemented in Python script. For minor/major, edit version files manually."
}

Write-Host "==> Bumping version..." -ForegroundColor Cyan
$bumpOutput = python "$PSScriptRoot/bump-version.py"
$newVersion = ($bumpOutput | Select-String 'New version: ([\d.]+)').Matches.Groups[1].Value
if (-not $newVersion) {
    throw "Failed to parse new version from bump script output"
}
Write-Host "    New version: $newVersion" -ForegroundColor Green

# 2. Stage version files
$versionFiles = @(
    "version.py",
    "version.iss",
    "src-tauri/Cargo.toml",
    "src-tauri/tauri.conf.json",
    "src-tauri/src/main.rs"
)
git add $versionFiles

# 3. Commit
$commitMsg = if ($Message) { $Message } else { "chore: bump version to $newVersion" }
Write-Host "==> Committing..." -ForegroundColor Cyan
git commit -m $commitMsg

# 4. Create annotated tag
$tagName = "v1.0.0-beta$([int]([version]$newVersion).Build + 1)"  # simple heuristic
# Better: use semantic version tag
$tagName = "v$newVersion"
Write-Host "==> Creating tag $tagName..." -ForegroundColor Cyan
git tag -a $tagName -m "Release $newVersion"

# 5. Push
if ($Push) {
    $branch = git rev-parse --abbrev-ref HEAD
    Write-Host "==> Pushing to $Remote/$branch..." -ForegroundColor Cyan
    git push $Remote $branch
    Write-Host "==> Pushing tag $tagName..." -ForegroundColor Cyan
    git push $Remote $tagName
    Write-Host "Done!" -ForegroundColor Green
} else {
    Write-Host "Skipped push (use -Push to enable)." -ForegroundColor Yellow
    Write-Host "Run manually: git push $Remote $(git rev-parse --abbrev-ref HEAD) && git push $Remote $tagName"
}