# Hydro Suite Branch Guide

This document explains the different versions of Hydro Suite and how to work with them.

## 🌿 **Branch Structure**

### **`master` branch - Standalone Version**
- **Purpose**: Traditional standalone QGIS script application
- **Launch**: Via QGIS Python Console
- **Target Users**: Power users, developers, testing
- **Installation**: No installation required

**Repository**: https://github.com/Jwoody124/hydro-suite

### **`plugin-version` branch - QGIS Plugin**
- **Purpose**: Native QGIS plugin integration
- **Launch**: Via QGIS Plugins menu/toolbar
- **Target Users**: End users, production environments
- **Installation**: Copy to QGIS plugins directory

**Repository**: https://github.com/Jwoody124/hydro-suite/tree/plugin-version

## 📋 **Version Comparison**

| Feature | Standalone (master) | Plugin (plugin-version) |
|---------|-------------------|------------------------|
| **Launch Method** | Python Console | Plugin Menu/Toolbar |
| **Installation** | Script execution | Plugin directory copy |
| **QGIS Integration** | External window | Native integration |
| **Updates** | Git pull | Plugin manager |
| **Distribution** | GitHub clone | ZIP package |
| **Target Audience** | Developers/Power users | End users |
| **Maintenance** | Git workflow | Plugin repository |

## 🚀 **Working with Both Versions**

### **Switch Between Branches**
```bash
# Work on standalone version
git checkout master
git pull origin master

# Work on plugin version  
git checkout plugin-version
git pull origin plugin-version
```

### **Apply Changes to Both Versions**

#### **Method 1: Cherry-pick specific commits**
```bash
# Make changes in master branch
git checkout master
# ... make changes ...
git commit -m "Fix validation bug in CN Calculator"

# Apply same fix to plugin branch
git checkout plugin-version
git cherry-pick <commit-hash>
git push origin plugin-version
```

#### **Method 2: Merge between branches (for major updates)**
```bash
# Update plugin with changes from master
git checkout plugin-version
git merge master
# Resolve any conflicts
git push origin plugin-version
```

## 🔧 **Development Workflows**

### **Standalone Development (master branch)**
```bash
git checkout master
git pull origin master

# Make changes to core files
# Test with: exec(open('fixed_launch.py').read())

git add .
git commit -m "Description of changes"
git push origin master
```

### **Plugin Development (plugin-version branch)**
```bash
git checkout plugin-version
git pull origin plugin-version

# Make changes to hydro_suite_plugin/ files
# Test by installing in QGIS

git add .
git commit -m "Description of plugin changes"
git push origin plugin-version
```

### **Feature Development (affects both versions)**
```bash
# Create feature branch from master
git checkout master
git checkout -b feature/new-storm-tool

# Develop feature
# ... make changes ...
git commit -m "Add storm sewer analysis tool"

# Merge to master
git checkout master
git merge feature/new-storm-tool
git push origin master

# Apply to plugin version
git checkout plugin-version
git cherry-pick <feature-commits>
# Copy new files to hydro_suite_plugin/ if needed
git push origin plugin-version

# Clean up
git branch -d feature/new-storm-tool
```

## 📦 **Distribution**

### **Standalone Version Distribution**
```bash
# Users clone the repository
git clone https://github.com/Jwoody124/hydro-suite.git
cd hydro-suite/Hydro_Suite_Data
# Launch in QGIS console
```

### **Plugin Version Distribution**

#### **For Development/Testing:**
```bash
# Get plugin files
git clone -b plugin-version https://github.com/Jwoody124/hydro-suite.git
cd hydro-suite/Hydro_Suite_Data
cp -r hydro_suite_plugin/ "C:/Users/[username]/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/"
```

#### **For End Users (ZIP package):**
```bash
# Create distribution ZIP
git checkout plugin-version
cd hydro_suite_plugin
zip -r hydro_suite_plugin.zip .
# Distribute the ZIP file
```

## 🎯 **When to Use Each Branch**

### **Use Standalone Version (`master`) When:**
- ✅ Developing new features
- ✅ Testing and debugging
- ✅ Working with multiple AI tools
- ✅ Need direct access to Python console
- ✅ Customizing for specific projects

### **Use Plugin Version (`plugin-version`) When:**
- ✅ Deploying to end users
- ✅ Publishing to QGIS Plugin Repository
- ✅ Need native QGIS integration
- ✅ Want automatic plugin management
- ✅ Distributing to non-technical users

## 🔄 **Synchronization Strategy**

### **Primary Development**: Always in `master` branch
### **Plugin Updates**: Regular sync from `master` to `plugin-version`

```bash
# Weekly sync workflow
git checkout master
git pull origin master

git checkout plugin-version
git pull origin plugin-version

# Merge new features from master
git merge master

# Update plugin-specific files if needed
# Test plugin installation

git push origin plugin-version
```

## 📝 **Commit Message Conventions**

### **Standalone commits (master):**
```bash
git commit -m "Add detention pond calculator"
git commit -m "Fix CN validation bug" 
git commit -m "Update documentation"
```

### **Plugin commits (plugin-version):**
```bash
git commit -m "[PLUGIN] Update metadata for v1.1 release"
git commit -m "[PLUGIN] Fix icon loading issue"
git commit -m "[PLUGIN] Sync with master: Add detention pond tool"
```

## 🚨 **Important Notes**

1. **Always test both versions** when making core changes
2. **Plugin directory structure** must be maintained in plugin-version
3. **Don't merge plugin-version back to master** (it contains plugin-specific files)
4. **Icon requirements** differ between versions
5. **Documentation** should be updated in both branches when relevant

## 📞 **Quick Reference Commands**

```bash
# Switch to standalone development
git checkout master && git pull origin master

# Switch to plugin development  
git checkout plugin-version && git pull origin plugin-version

# Sync plugin with standalone
git checkout plugin-version && git merge master

# Create feature branch
git checkout master && git checkout -b feature/tool-name

# View branch differences
git diff master..plugin-version

# See current branch
git branch
```

---

This structure ensures both versions remain functional while allowing independent development and distribution strategies.