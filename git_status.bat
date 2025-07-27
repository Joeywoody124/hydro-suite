@echo off
echo ==========================================
echo     Hydro Suite - Git Status Check
echo ==========================================
echo.

:: Navigate to project directory
cd /d "E:\CLAUDE_Workspace\Claude\Report_Files\Codebase\Hydro_Suite\Hydro_Suite_Data"

:: Show current branch
echo Current branch:
git branch --show-current
echo.

:: Show all branches
echo All branches:
git branch -a
echo.

:: Show status of current branch
echo Current branch status:
git status
echo.

:: Show recent commits
echo Recent commits (last 10):
git log --oneline -10
echo.

:: Show any uncommitted changes
echo Uncommitted changes:
git diff --name-only
if errorlevel 1 (
    echo No uncommitted changes.
)
echo.

:: Show staged changes
echo Staged changes:
git diff --staged --name-only
if errorlevel 1 (
    echo No staged changes.
)
echo.

echo Remote URLs:
git remote -v
echo.

pause