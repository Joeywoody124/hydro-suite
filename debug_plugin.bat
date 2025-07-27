@echo off
echo ==========================================
echo    Hydro Suite - Plugin Debug Helper
echo ==========================================
echo.

:: Navigate to project directory
cd /d "E:\CLAUDE_Workspace\Claude\Report_Files\Codebase\Hydro_Suite\Hydro_Suite_Data"

:: Switch to plugin branch
git checkout plugin-version

:: Check plugin files
echo Checking plugin directory structure...
echo.
if exist "hydro_suite_plugin" (
    echo ✅ Plugin directory exists
    dir /b hydro_suite_plugin
) else (
    echo ❌ Plugin directory missing!
    pause
    exit /b 1
)

echo.
echo Checking critical plugin files:

if exist "hydro_suite_plugin\__init__.py" (
    echo ✅ __init__.py exists
) else (
    echo ❌ __init__.py missing!
)

if exist "hydro_suite_plugin\metadata.txt" (
    echo ✅ metadata.txt exists
) else (
    echo ❌ metadata.txt missing!
)

if exist "hydro_suite_plugin\hydro_suite.py" (
    echo ✅ hydro_suite.py exists
) else (
    echo ❌ hydro_suite.py missing!
)

echo.
echo Plugin metadata content:
echo ----------------------------------------
type hydro_suite_plugin\metadata.txt
echo ----------------------------------------
echo.

echo QGIS Plugin Directory Location:
echo %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\hydro_suite_plugin
echo.

if exist "%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\hydro_suite_plugin" (
    echo ✅ Plugin installed in QGIS
    echo Installed files:
    dir /b "%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\hydro_suite_plugin"
) else (
    echo ❌ Plugin not installed in QGIS
    echo Run install_plugin.bat to install
)

echo.
echo Next steps for debugging:
echo 1. Open QGIS
echo 2. Open Python Console (Plugins → Python Console)
echo 3. Run this command to check for errors:
echo    import hydro_suite_plugin
echo 4. If errors appear, note the specific error message
echo.

pause