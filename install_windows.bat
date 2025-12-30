@echo off
REM ============================================
REM ALUSTECK BUILDER - WINDOWS INSTALLATION
REM ============================================
REM Automatische Installation für Windows

setlocal enabledelayedexpansion

echo.
echo ============================================
echo ALUSTECK BUILDER - WINDOWS INSTALLER
echo ============================================
echo.

REM Blender Installationen suchen
set "BLENDER_FOUND=0"
set "BLENDER_PATHS="

REM Häufige Blender Installationsorte auf Windows
set "SEARCH_PATHS[0]=%ProgramFiles%\Blender Foundation"
set "SEARCH_PATHS[1]=%ProgramFiles(x86)%\Blender Foundation"
set "SEARCH_PATHS[2]=%LocalAppData%\Programs\Blender"
set "SEARCH_PATHS[3]=C:\Blender"

echo [1] Suche nach Blender Installationen...
echo.

for /L %%i in (0,1,3) do (
    if exist "!SEARCH_PATHS[%%i]!" (
        echo   Found: !SEARCH_PATHS[%%i]!
        set "BLENDER_FOUND=1"
    )
)

if !BLENDER_FOUND! equ 0 (
    echo.
    echo [ERROR] Blender nicht gefunden!
    echo.
    echo Mögliche Lösungen:
    echo 1. Blender von https://www.blender.org/ herunterladen
    echo 2. Blender installieren
    echo 3. Dieses Skript erneut ausführen
    echo.
    pause
    exit /b 1
)

echo.
echo [2] Bestimme Blender AppData Verzeichnis...
echo.

REM Blender Versions-Ordner im AppData suchen
for /d %%d in ("%APPDATA%\Blender\*") do (
    if exist "%%d\scripts\addons" (
        echo   Found Blender version: %%~nxd
        set "BLENDER_VERSION=%%~nxd"
    )
)

if not defined BLENDER_VERSION (
    echo [WARNING] Blender AppData Verzeichnis nicht gefunden!
    echo.
    echo Versuche manuell zu erstellen...
    set "BLENDER_VERSION=4.2"
)

echo   Using version: !BLENDER_VERSION!

set "ADDONS_DIR=%APPDATA%\Blender\!BLENDER_VERSION!\scripts\addons"

echo.
echo [3] Kopiere Addon in: !ADDONS_DIR!
echo.

if not exist "!ADDONS_DIR!" (
    echo   Erstelle Verzeichnis...
    mkdir "!ADDONS_DIR!" || (
        echo [ERROR] Konnte Verzeichnis nicht erstellen
        pause
        exit /b 1
    )
)

REM Aktuelle Addon-Quelle
set "ADDON_SRC=%~dp0alusteck_builder"

if not exist "!ADDON_SRC!" (
    echo [ERROR] Addon-Ordner nicht gefunden: !ADDON_SRC!
    pause
    exit /b 1
)

echo   Quelle: !ADDON_SRC!

REM Kopiere Addon
echo   Kopiere Dateien...
xcopy "!ADDON_SRC!" "!ADDONS_DIR!\alusteck_builder" /E /I /Y > nul

if !errorlevel! equ 0 (
    echo.
    echo ============================================
    echo ✅ INSTALLATION ERFOLGREICH!
    echo ============================================
    echo.
    echo Addon-Pfad:
    echo   !ADDONS_DIR!\alusteck_builder
    echo.
    echo Nächste Schritte:
    echo 1. Starte Blender
    echo 2. Gehe zu: Edit ^> Preferences ^> Add-ons
    echo 3. Suche nach: "Alusteck"
    echo 4. Aktiviere das Addon (Häkchen setzen)
    echo 5. Speichere Preferences (speichern Button oben rechts)
    echo.
    echo Optional:
    echo - Claude API Key eingeben für AI-Features
    echo   (Edit ^> Preferences ^> Add-ons ^> Alusteck ^> API Key)
    echo.
) else (
    echo.
    echo [ERROR] Fehler beim Kopieren!
    echo.
)

pause
