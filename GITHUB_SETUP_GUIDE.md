# GitHub Setup Guide for Hydro Suite

This guide will walk you through pushing the Hydro Suite project to GitHub.

## Prerequisites
- GitHub account (create one at https://github.com if needed)
- Git installed on your computer

## Step 1: Create a New Repository on GitHub

1. Go to https://github.com
2. Click the "+" icon in the top right → "New repository"
3. Configure the repository:
   - **Repository name**: `hydro-suite` (or your preferred name)
   - **Description**: "QGIS Hydrological Analysis Toolbox - A comprehensive toolbox for watershed modeling and stormwater analysis"
   - **Public/Private**: Choose based on your preference
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
4. Click "Create repository"

## Step 2: Connect Local Repository to GitHub

Open a terminal/command prompt and navigate to your project:

```bash
cd E:\CLAUDE_Workspace\Claude\Report_Files\Codebase\Hydro_Suite\Hydro_Suite_Data
```

### First-time Git setup (if needed):
```bash
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

### Add GitHub as remote origin:
```bash
# Replace YOUR_USERNAME with your GitHub username
git remote add origin https://github.com/YOUR_USERNAME/hydro-suite.git

# Verify the remote was added
git remote -v
```

## Step 3: Push to GitHub

### Add the new files we created:
```bash
git add .gitignore README.md LICENSE GITHUB_SETUP_GUIDE.md
git commit -m "Add GitHub-specific files: README, LICENSE, .gitignore"
```

### Push everything to GitHub:
```bash
# Push to main branch
git push -u origin master

# If your default branch is 'main' instead of 'master':
git branch -M main
git push -u origin main
```

## Step 4: Verify on GitHub

1. Go to your repository: `https://github.com/YOUR_USERNAME/hydro-suite`
2. You should see all your files
3. The README.md will be displayed on the main page

## Optional: Add Topics and Settings

### Add topics to help people find your project:
1. Go to your repository page
2. Click the gear icon next to "About"
3. Add topics like: `qgis`, `hydrology`, `python`, `gis`, `stormwater`, `watershed`

### Configure repository settings:
1. Go to Settings → General
2. Features to consider enabling:
   - Issues (for bug reports)
   - Discussions (for Q&A)
   - Projects (for roadmap tracking)

## Troubleshooting

### If you get authentication errors:

#### Option 1: Use Personal Access Token (Recommended)
1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token with 'repo' scope
3. Use the token as your password when pushing

#### Option 2: Use GitHub CLI
```bash
# Install GitHub CLI from https://cli.github.com/
gh auth login
```

#### Option 3: Use SSH
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your-email@example.com"

# Add to GitHub account
# Copy the public key and add to GitHub → Settings → SSH keys

# Change remote to SSH
git remote set-url origin git@github.com:YOUR_USERNAME/hydro-suite.git
```

### If you need to remove sensitive data:
```bash
# If you accidentally committed sensitive data
git rm --cached filename
echo "filename" >> .gitignore
git commit -m "Remove sensitive file"
```

## Best Practices

1. **Branch Protection**: Consider protecting your main branch
   - Settings → Branches → Add rule
   - Require pull request reviews before merging

2. **Releases**: Tag versions for users
   ```bash
   git tag -a v1.0.0 -m "Initial release"
   git push origin v1.0.0
   ```

3. **Documentation**: Keep README.md updated with:
   - Installation instructions
   - Usage examples
   - Screenshots (add to a `docs/images/` folder)

4. **Issues Templates**: Create templates for bug reports and feature requests
   - Create `.github/ISSUE_TEMPLATE/` directory
   - Add bug_report.md and feature_request.md

## Next Steps

1. Share your repository link
2. Add collaborators if working with others
3. Set up GitHub Actions for automated testing (optional)
4. Consider adding example data in an `examples/` folder
5. Add screenshots to make the README more visual

## Example Repository URL

Once pushed, your repository will be available at:
```
https://github.com/YOUR_USERNAME/hydro-suite
```

Users can then clone it with:
```bash
git clone https://github.com/YOUR_USERNAME/hydro-suite.git
```

---

**Note**: Remember to update YOUR_USERNAME with your actual GitHub username in all commands above!