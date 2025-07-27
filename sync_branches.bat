@echo off
echo ==========================================
echo    Hydro Suite - Sync Plugin with Main
echo ==========================================
echo.

:: Navigate to project directory
cd /d "E:\CLAUDE_Workspace\Claude\Report_Files\Codebase\Hydro_Suite\Hydro_Suite_Data"

:: Update main branch first
echo Step 1: Updating main branch...
git checkout main
if errorlevel 1 (
    echo ERROR: Failed to switch to main branch
    pause
    exit /b 1
)

git pull origin main
if errorlevel 1 (
    echo ERROR: Failed to pull main branch
    pause
    exit /b 1
)

:: Switch to plugin branch
echo Step 2: Switching to plugin-version branch...
git checkout plugin-version
if errorlevel 1 (
    echo ERROR: Failed to switch to plugin-version branch
    pause
    exit /b 1
)

git pull origin plugin-version
if errorlevel 1 (
    echo ERROR: Failed to pull plugin-version branch
    pause
    exit /b 1
)

:: Merge main into plugin-version
echo Step 3: Merging main branch changes into plugin-version...
git merge main
if errorlevel 1 (
    echo.
    echo ⚠️  MERGE CONFLICT DETECTED!
    echo Please resolve conflicts manually and then run:
    echo   git add .
    echo   git commit -m "[PLUGIN] Sync with main branch"
    echo   git push origin plugin-version
    echo.
    pause
    exit /b 1
)

:: Copy updated core files to plugin directory
echo Step 4: Syncing core files to plugin directory...
copy /Y hydro_suite_main.py hydro_suite_plugin\hydro_suite_main.py
copy /Y hydro_suite_interface.py hydro_suite_plugin\hydro_suite_interface.py
copy /Y shared_widgets.py hydro_suite_plugin\shared_widgets.py
copy /Y cn_calculator_tool.py hydro_suite_plugin\cn_calculator_tool.py
copy /Y rational_c_tool.py hydro_suite_plugin\rational_c_tool.py
copy /Y tc_calculator_tool.py hydro_suite_plugin\tc_calculator_tool.py
copy /Y channel_designer_tool.py hydro_suite_plugin\channel_designer_tool.py

:: Check if there are changes to commit
git add .
git diff --staged --quiet
if errorlevel 1 (
    echo Step 5: Committing synchronized changes...
    git commit -m "[PLUGIN] Sync with main branch - updated core files"
    if errorlevel 1 (
        echo ERROR: Failed to commit changes
        pause
        exit /b 1
    )
    
    :: Push changes
    echo Step 6: Pushing synchronized changes...
    git push origin plugin-version
    if errorlevel 1 (
        echo ERROR: Failed to push changes
        pause
        exit /b 1
    )
    
    echo.
    echo ✅ SUCCESS: Plugin branch synchronized with main!
    echo Main: https://github.com/Jwoody124/hydro-suite
    echo Plugin: https://github.com/Jwoody124/hydro-suite/tree/plugin-version
    
) else (
    echo Plugin branch is already up to date with main.
)

echo.
echo Current plugin status:
git status --short

echo.
pause