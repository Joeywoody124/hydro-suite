# Hydro Suite Batch Files Guide

This folder contains convenient batch files for common Git and plugin operations.

## 📋 **Available Batch Files**

### **quick_push_main.bat**
- **Purpose**: Quick push changes to main branch (standalone version)
- **What it does**:
  - Switches to main branch
  - Pulls latest changes
  - Adds all modified files
  - Prompts for commit message
  - Commits and pushes to GitHub

**Usage**: Double-click or run from command line
```cmd
quick_push_main.bat
```

### **quick_push_plugin.bat**
- **Purpose**: Quick push changes to plugin-version branch
- **What it does**:
  - Switches to plugin-version branch
  - Pulls latest changes
  - Adds all modified files
  - Prompts for commit message (adds [PLUGIN] prefix)
  - Commits and pushes to GitHub

**Usage**: Double-click or run from command line
```cmd
quick_push_plugin.bat
```

### **sync_branches.bat**
- **Purpose**: Synchronize plugin branch with latest main branch changes
- **What it does**:
  - Updates main branch
  - Switches to plugin-version branch
  - Merges main into plugin-version
  - Copies updated core files to plugin directory
  - Commits and pushes synchronized changes

**Usage**: Run when main branch has new features to add to plugin
```cmd
sync_branches.bat
```

### **git_status.bat**
- **Purpose**: Check current Git status and branch information
- **What it does**:
  - Shows current branch
  - Lists all branches
  - Shows status and recent commits
  - Displays uncommitted/staged changes
  - Shows remote URLs

**Usage**: Quick status check
```cmd
git_status.bat
```

### **install_plugin.bat**
- **Purpose**: Install plugin directly to QGIS
- **What it does**:
  - Switches to plugin-version branch
  - Pulls latest plugin updates
  - Copies plugin files to QGIS plugins directory
  - Provides installation instructions

**Usage**: Install/update plugin in QGIS
```cmd
install_plugin.bat
```

## 🔄 **Common Workflows**

### **Daily Development**
1. Check status: `git_status.bat`
2. Make your changes
3. Push to appropriate branch:
   - For standalone: `quick_push_main.bat`
   - For plugin: `quick_push_plugin.bat`

### **Weekly Sync**
1. After adding features to main branch
2. Run: `sync_branches.bat`
3. Test plugin: `install_plugin.bat`

### **Plugin Testing**
1. Make changes to plugin files
2. Push changes: `quick_push_plugin.bat`
3. Install in QGIS: `install_plugin.bat`
4. Test in QGIS

## ⚠️ **Important Notes**

### **Prerequisites**
- Git must be installed and in PATH
- You must be in the correct directory when running
- GitHub authentication must be set up

### **Error Handling**
- All batch files include error checking
- They will pause on errors for you to review
- Failed operations won't continue to prevent data loss

### **Path Requirements**
- Batch files use absolute paths to project directory
- Modify the path in each file if you move the project:
  ```cmd
  cd /d "E:\CLAUDE_Workspace\Claude\Report_Files\Codebase\Hydro_Suite\Hydro_Suite_Data"
  ```

### **QGIS Plugin Directory**
- Windows: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins`
- The `install_plugin.bat` automatically detects this location
- QGIS must be run at least once to create the directory

## 🛠️ **Customization**

### **Modify Commit Message Format**
Edit the commit line in each batch file:
```cmd
git commit -m "Your custom format: %commit_msg%"
```

### **Change Default Paths**
Update the `cd` command in each file:
```cmd
cd /d "YOUR_PROJECT_PATH"
```

### **Add Custom Operations**
You can extend any batch file with additional commands:
```cmd
:: Add after the main operations
echo Running tests...
python test_complete_framework.py
```

## 🚀 **Quick Reference**

| Task | Command |
|------|---------|
| Push standalone changes | `quick_push_main.bat` |
| Push plugin changes | `quick_push_plugin.bat` |
| Sync plugin with main | `sync_branches.bat` |
| Check Git status | `git_status.bat` |
| Install plugin to QGIS | `install_plugin.bat` |

## 🔧 **Troubleshooting**

### **"Git command not found"**
- Install Git for Windows
- Add Git to system PATH
- Restart command prompt

### **"Access denied" errors**
- Run as Administrator
- Check file permissions
- Ensure QGIS is closed when installing plugin

### **"Failed to push" errors**
- Check GitHub authentication
- Verify internet connection
- Make sure you have push permissions to repository

### **Plugin not appearing in QGIS**
1. Check plugin was copied correctly
2. Restart QGIS
3. Enable plugin in Plugin Manager
4. Check QGIS Python Console for errors

---

**Tip**: Create desktop shortcuts to these batch files for even quicker access!