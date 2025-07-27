@echo off
echo ==========================================
echo    Hydro Suite - Quick Push to Main
echo ==========================================
echo.

:: Navigate to project directory
cd /d "E:\CLAUDE_Workspace\Claude\Report_Files\Codebase\Hydro_Suite\Hydro_Suite_Data"

:: Switch to main branch
echo Switching to main branch...
git checkout main
if errorlevel 1 (
    echo ERROR: Failed to switch to main branch
    pause
    exit /b 1
)

:: Pull latest changes
echo Pulling latest changes...
git pull origin main
if errorlevel 1 (
    echo ERROR: Failed to pull latest changes
    pause
    exit /b 1
)

:: Add all changes
echo Adding all changes...
git add .

:: Check if there are changes to commit
git diff --staged --quiet
if errorlevel 1 (
    echo Changes detected, preparing commit...
    
    :: Prompt for commit message
    set /p commit_msg="Enter commit message: "
    if "%commit_msg%"=="" (
        echo ERROR: Commit message cannot be empty
        pause
        exit /b 1
    )
    
    :: Commit changes
    echo Committing changes...
    git commit -m "%commit_msg%"
    if errorlevel 1 (
        echo ERROR: Failed to commit changes
        pause
        exit /b 1
    )
    
    :: Push to GitHub
    echo Pushing to GitHub...
    git push origin main
    if errorlevel 1 (
        echo ERROR: Failed to push to GitHub
        pause
        exit /b 1
    )
    
    echo.
    echo ✅ SUCCESS: Changes pushed to main branch!
    echo Repository: https://github.com/Jwoody124/hydro-suite
    
) else (
    echo No changes to commit.
)

echo.
echo Current status:
git status --short

echo.
echo Recent commits:
git log --oneline -5

echo.
pause