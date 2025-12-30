#!/usr/bin/env powershell
# ============================================
# ALUSTECK BUILDER - WINDOWS INSTALLATION
# ============================================
# PowerShell Version (Modern Windows)
#
# Usage:
#   Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
#   .\install_windows.ps1

Write-Host "`n============================================`n" -ForegroundColor Cyan
Write-Host "ALUSTECK BUILDER - WINDOWS INSTALLER" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

# Admin Check
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

# Häufige Blender Installationsorte
$blenderSearchPaths = @(
    "$env:ProgramFiles\Blender Foundation",
    "${env:ProgramFiles(x86)}\Blender Foundation",
    "$env:LocalAppData\Programs\Blender",
    "C:\Blender"
)

Write-Host "[1] Suche nach Blender Installationen..." -ForegroundColor Yellow
$blenderFound = $false

foreach ($path in $blenderSearchPaths) {
    if (Test-Path $path) {
        Write-Host "   ✓ Found: $path" -ForegroundColor Green
        $blenderFound = $true
    }
}

if (-not $blenderFound) {
    Write-Host "`n[ERROR] Blender nicht gefunden!`n" -ForegroundColor Red
    Write-Host "Lösungen:" -ForegroundColor Yellow
    Write-Host "1. Download: https://www.blender.org/" 
    Write-Host "2. Install Blender"
    Write-Host "3. Rerun this script"
    Read-Host "Press Enter to exit"
    exit 1
}

# Blender AppData Verzeichnis
Write-Host "`n[2] Bestimme Blender AppData Verzeichnis..." -ForegroundColor Yellow

$blenderVersionsPath = "$env:APPDATA\Blender"

if (-not (Test-Path $blenderVersionsPath)) {
    Write-Host "   ⚠ Blender AppData nicht gefunden!" -ForegroundColor Yellow
    Write-Host "   Erstelle: $blenderVersionsPath"
    New-Item -ItemType Directory -Force -Path $blenderVersionsPath | Out-Null
}

# Finde neueste Blender Version
$blenderVersion = $null
if (Test-Path $blenderVersionsPath) {
    $versions = Get-ChildItem -Path $blenderVersionsPath -Directory | 
    Where-Object { $_.Name -match '^\d+\.\d+$' } | 
    Sort-Object Name -Descending
    
    if ($versions) {
        $blenderVersion = $versions[0].Name
        Write-Host "   ✓ Found Blender: $blenderVersion" -ForegroundColor Green
    }
}

if (-not $blenderVersion) {
    $blenderVersion = "4.2"
    Write-Host "   ⚠ Using default version: $blenderVersion" -ForegroundColor Yellow
}

# Addon Directory
$addonsDir = "$env:APPDATA\Blender\$blenderVersion\scripts\addons"

Write-Host "`n[3] Kopiere Addon..." -ForegroundColor Yellow
Write-Host "   Target: $addonsDir" -ForegroundColor Cyan

# Stelle sicher dass Addon-Dir existiert
if (-not (Test-Path $addonsDir)) {
    Write-Host "   Erstelle Verzeichnis..." -ForegroundColor Cyan
    try {
        New-Item -ItemType Directory -Force -Path $addonsDir | Out-Null
        Write-Host "   ✓ Created" -ForegroundColor Green
    }
    catch {
        Write-Host "   ✗ Fehler: $_" -ForegroundColor Red
        if (-not $isAdmin) {
            Write-Host "`n⚠ Admin-Rechte erforderlich!`n" -ForegroundColor Yellow
            Write-Host "Lösung:" -ForegroundColor Yellow
            Write-Host "- Rechtsklick auf install_windows.ps1"
            Write-Host "- 'Run with PowerShell' auswählen"
            Write-Host "- 'Ja' bei UAC-Prompt klicken"
        }
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Addon Source
$addonSrc = "$PSScriptRoot\alusteck_builder"

if (-not (Test-Path $addonSrc)) {
    Write-Host "   ✗ Addon nicht gefunden: $addonSrc" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "   Source: $addonSrc" -ForegroundColor Cyan

# Copy Addon
Write-Host "   Kopiere Dateien..." -ForegroundColor Cyan
$addonTarget = "$addonsDir\alusteck_builder"

# Lösche alte Version falls existiert
if (Test-Path $addonTarget) {
    Write-Host "   Lösche alte Version..." -ForegroundColor Cyan
    Remove-Item -Recurse -Force $addonTarget
}

# Kopiere
try {
    Copy-Item -Path $addonSrc -Destination $addonTarget -Recurse -Force
    Write-Host "   ✓ Copied" -ForegroundColor Green
}
catch {
    Write-Host "   ✗ Fehler: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Success Message
Write-Host "`n============================================" -ForegroundColor Green
Write-Host "✅ INSTALLATION ERFOLGREICH!" -ForegroundColor Green
Write-Host "============================================`n" -ForegroundColor Green

Write-Host "Addon-Pfad:" -ForegroundColor Cyan
Write-Host "   $addonTarget`n"

Write-Host "Nächste Schritte:" -ForegroundColor Yellow
Write-Host "1. Starte Blender"
Write-Host "2. Gehe zu: Edit > Preferences > Add-ons"
Write-Host "3. Suche nach: 'Alusteck'"
Write-Host "4. Aktiviere das Addon (Häkchen setzen)"
Write-Host "5. Speichere Preferences`n"

Write-Host "Optional:" -ForegroundColor Yellow
Write-Host "- Claude API Key eingeben für AI-Features"
Write-Host "  (Edit > Preferences > Add-ons > Alusteck > Claude API Key)"
Write-Host ""

Read-Host "Press Enter to exit"
