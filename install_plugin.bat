@echo off
echo ==========================================
echo   Hydro Suite - Install QGIS Plugin
echo ==========================================
echo.

:: Navigate to project directory
cd /d "E:\CLAUDE_Workspace\Claude\Report_Files\Codebase\Hydro_Suite\Hydro_Suite_Data"

:: Check if we're on plugin branch
git branch --show-current | findstr "plugin-version" >nul
if errorlevel 1 (
    echo Switching to plugin-version branch...
    git checkout plugin-version
    if errorlevel 1 (
        echo ERROR: Failed to switch to plugin-version branch
        pause
        exit /b 1
    )
)

:: Pull latest plugin updates
echo Pulling latest plugin updates...
git pull origin plugin-version

:: Define QGIS plugin directory
set QGIS_PLUGINS_DIR=%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins
set TARGET_DIR=%QGIS_PLUGINS_DIR%\hydro_suite_plugin

echo.
echo QGIS Plugin Directory: %QGIS_PLUGINS_DIR%
echo Target Directory: %TARGET_DIR%

:: Check if QGIS plugins directory exists
if not exist "%QGIS_PLUGINS_DIR%" (
    echo ERROR: QGIS plugins directory not found!
    echo Expected: %QGIS_PLUGINS_DIR%
    echo.
    echo Please ensure QGIS is installed and has been run at least once.
    pause
    exit /b 1
)

:: Remove existing installation
if exist "%TARGET_DIR%" (
    echo Removing existing plugin installation...
    rmdir /s /q "%TARGET_DIR%"
)

:: Create plugin directory
echo Creating plugin directory...
mkdir "%TARGET_DIR%"

:: Copy plugin files
echo Copying plugin files...
xcopy /E /I /Y "hydro_suite_plugin\*" "%TARGET_DIR%"

if errorlevel 1 (
    echo ERROR: Failed to copy plugin files
    pause
    exit /b 1
)

echo.
echo ✅ SUCCESS: Hydro Suite plugin installed!
echo.
echo Next steps:
echo 1. Open QGIS
echo 2. Go to: Plugins → Manage and Install Plugins
echo 3. Click "Installed" tab
echo 4. Find "Hydro Suite" and check the box to enable
echo 5. Look for Hydro Suite icon in toolbar or Plugins menu
echo.
echo Plugin location: %TARGET_DIR%
echo.

:: Check if icon exists
if not exist "%TARGET_DIR%\icon.png" (
    echo ⚠️  NOTE: Custom icon not found. Plugin will use default QGIS icon.
    echo To add custom icon: Place 24x24 pixel PNG as 'icon.png' in plugin folder.
    echo.
)

pause