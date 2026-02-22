# Git Commands Quick Reference

## 🚀 Initial Setup (One Time)

```bash
# Navigate to project
cd crypto_levels_bhushan

# Initialize git (already done)
git init

# Add all files
git add .

# First commit
git commit -m "Initial commit: Premium trading dashboard"

# Add remote repository
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## 📝 Daily Workflow

### Check Status
```bash
git status                    # See what changed
git status --short            # Compact view
git status --ignored          # Show ignored files
```

### Add Changes
```bash
git add .                     # Add all changes
git add filename.js           # Add specific file
git add src/                  # Add directory
```

### Commit Changes
```bash
git commit -m "Your message"  # Commit with message
git commit -am "Message"      # Add + commit (tracked files only)
```

### Push to GitHub
```bash
git push                      # Push to current branch
git push origin main          # Push to main branch
```

### Pull from GitHub
```bash
git pull                      # Pull latest changes
git pull origin main          # Pull from main branch
```

---

## 🌿 Branching

### Create Branch
```bash
git branch feature-name       # Create branch
git checkout feature-name     # Switch to branch
git checkout -b feature-name  # Create + switch
```

### Switch Branches
```bash
git checkout main             # Switch to main
git checkout feature-name     # Switch to feature
```

### Merge Branches
```bash
git checkout main             # Switch to main
git merge feature-name        # Merge feature into main
```

### Delete Branch
```bash
git branch -d feature-name    # Delete local branch
git push origin --delete feature-name  # Delete remote branch
```

---

## 📜 History

### View Commits
```bash
git log                       # Full history
git log --oneline             # Compact history
git log --graph               # Visual graph
git log -5                    # Last 5 commits
```

### View Changes
```bash
git diff                      # Unstaged changes
git diff --staged             # Staged changes
git diff HEAD                 # All changes
git diff filename.js          # Specific file
```

---

## ↩️ Undo Changes

### Unstage Files
```bash
git reset filename.js         # Unstage specific file
git reset                     # Unstage all files
```

### Discard Changes
```bash
git checkout -- filename.js   # Discard changes in file
git checkout -- .             # Discard all changes
```

### Undo Last Commit
```bash
git reset --soft HEAD~1       # Keep changes staged
git reset --mixed HEAD~1      # Keep changes unstaged
git reset --hard HEAD~1       # Discard changes (⚠️ dangerous)
```

---

## 🔍 Inspection

### Show File
```bash
git show filename.js          # Show file content
git show HEAD:filename.js     # Show file at HEAD
```

### Blame (Who Changed What)
```bash
git blame filename.js         # Show who changed each line
```

### Search
```bash
git grep "search term"        # Search in tracked files
```

---

## 🏷️ Tags

### Create Tag
```bash
git tag v1.0.0                # Create tag
git tag -a v1.0.0 -m "Version 1.0.0"  # Annotated tag
```

### Push Tags
```bash
git push origin v1.0.0        # Push specific tag
git push origin --tags        # Push all tags
```

### List Tags
```bash
git tag                       # List all tags
git tag -l "v1.*"             # List matching tags
```

---

## 🔧 Configuration

### User Info
```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

### View Config
```bash
git config --list             # All settings
git config user.name          # Specific setting
```

### Aliases (Shortcuts)
```bash
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit

# Now you can use:
git st                        # Instead of git status
git co main                   # Instead of git checkout main
```

---

## 🆘 Common Issues

### Forgot to Add File
```bash
git add forgotten-file.js
git commit --amend --no-edit  # Add to last commit
```

### Wrong Commit Message
```bash
git commit --amend -m "Correct message"
```

### Merge Conflicts
```bash
# 1. Edit conflicted files
# 2. Remove conflict markers (<<<<, ====, >>>>)
# 3. Add resolved files
git add resolved-file.js
# 4. Complete merge
git commit
```

### Accidentally Committed .env
```bash
# Remove from git but keep file
git rm --cached backend/.env
git commit -m "Remove .env from git"

# Make sure .gitignore includes .env
echo ".env" >> .gitignore
git add .gitignore
git commit -m "Add .env to gitignore"
```

### Reset to Remote
```bash
git fetch origin
git reset --hard origin/main  # ⚠️ Discards local changes
```

---

## 📦 Stash (Temporary Save)

### Save Changes
```bash
git stash                     # Save changes
git stash save "Description"  # Save with message
```

### List Stashes
```bash
git stash list                # Show all stashes
```

### Apply Stash
```bash
git stash pop                 # Apply + remove latest
git stash apply               # Apply but keep stash
git stash apply stash@{0}     # Apply specific stash
```

### Delete Stash
```bash
git stash drop                # Delete latest
git stash drop stash@{0}      # Delete specific
git stash clear               # Delete all
```

---

## 🔄 Remote

### View Remotes
```bash
git remote -v                 # List remotes
```

### Add Remote
```bash
git remote add origin URL     # Add remote
```

### Change Remote URL
```bash
git remote set-url origin NEW_URL
```

### Remove Remote
```bash
git remote remove origin
```

---

## 📊 Statistics

### Contribution Stats
```bash
git shortlog -sn              # Commits per author
git shortlog -sn --all        # All branches
```

### File Changes
```bash
git diff --stat               # Files changed
git diff --shortstat          # Summary
```

### Repository Size
```bash
git count-objects -vH         # Repo size
```

---

## 🎯 Best Practices

### Commit Messages
```bash
# Good commit messages:
git commit -m "Add dark mode toggle to premium dashboard"
git commit -m "Fix MongoDB SSL connection error"
git commit -m "Update README with setup instructions"

# Bad commit messages:
git commit -m "fix"
git commit -m "update"
git commit -m "changes"
```

### Commit Often
```bash
# Small, focused commits are better than large ones
git add src/pages/Monitor_Premium.js
git commit -m "Add premium monitor component"

git add src/pages/Monitor_Premium.css
git commit -m "Add premium monitor styles"
```

### Pull Before Push
```bash
git pull                      # Get latest changes
# Resolve any conflicts
git push                      # Push your changes
```

---

## 🚨 Emergency Commands

### Undo Everything (⚠️ Dangerous)
```bash
git reset --hard HEAD         # Discard all changes
git clean -fd                 # Remove untracked files
```

### Recover Deleted Commit
```bash
git reflog                    # Find commit hash
git checkout HASH             # Recover commit
```

### Force Push (⚠️ Use with caution)
```bash
git push --force              # Overwrite remote
git push --force-with-lease   # Safer force push
```

---

## 📚 Learn More

### Help
```bash
git help                      # General help
git help commit               # Help for specific command
git commit --help             # Same as above
```

### Documentation
- Official Git Docs: https://git-scm.com/doc
- GitHub Guides: https://guides.github.com
- Git Cheat Sheet: https://education.github.com/git-cheat-sheet-education.pdf

---

## ✅ Your Current Setup

```bash
# Repository: crypto_levels_bhushan
# Branch: main
# Remote: (to be added)
# Files tracked: 37
# Files ignored: .env, node_modules, venv, __pycache__
```

---

*Git Commands Reference - Updated February 2, 2026*
