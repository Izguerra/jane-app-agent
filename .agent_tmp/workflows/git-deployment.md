---
description: Standard Git deployment workflow for all code changes
---

# Git Deployment Workflow

**IMPORTANT**: Always follow this workflow for ANY code changes, no matter how small.

## Branch Strategy

- `main` - Production branch (stable, deployed to production)
- `dev` - Development/Staging branch (testing before production)
- `feature/*` - Feature branches (all work happens here)

## Standard Workflow

### 1. Start New Work
```bash
# Always start from latest dev
git checkout dev
git pull origin dev

# Create feature branch with descriptive name
git checkout -b feature/your-feature-name
# Examples: feature/fix-voice-agent, feature/add-whatsapp-integration
```

### 2. Make Changes and Commit
```bash
# Make your code changes

# Stage changes
git add .

# Commit with descriptive message
git commit -m "Type: Brief description

Detailed explanation of what changed and why.
- Bullet point 1
- Bullet point 2"

# Types: Fix, Feature, Refactor, Security, Docs, Test, Chore
```

### 3. Push Feature Branch
```bash
# Push to GitHub
git push -u origin feature/your-feature-name
```

### 4. Create Pull Request
```bash
# Option 1: Use GitHub CLI (if available)
gh pr create --base dev --title "Your PR Title" --body "Description"

# Option 2: Go to GitHub web interface
# - Visit: https://github.com/supaagent/aicustomersupport
# - Click "Compare & pull request" button
# - Set base branch to: dev
# - Add title and description
# - Click "Create pull request"
```

### 5. Review and Merge
- Review the changes in the PR
- Check for conflicts
- Merge into `dev` when ready
- Delete the feature branch after merge

### 6. Deploy to Production (when ready)
```bash
# Create PR from dev to main
# Only do this when dev is stable and tested

# Option 1: GitHub CLI
gh pr create --base main --head dev --title "Release: [version/date]" --body "Production deployment"

# Option 2: GitHub web interface
# - Create PR from dev → main
# - Get approval
# - Merge to main
```

## Quick Reference

### Emergency Hotfix
```bash
# For critical production fixes
git checkout main
git pull origin main
git checkout -b hotfix/critical-fix-name
# Make fix
git commit -m "Hotfix: Description"
git push -u origin hotfix/critical-fix-name
# Create PR to main
# After merge, also merge main back to dev
```

### Check Current Status
```bash
git status                    # See current changes
git branch                    # See all branches
git log --oneline -5          # See recent commits
```

### Undo Changes
```bash
git restore <file>            # Discard changes in file
git restore .                 # Discard all changes
git reset --soft HEAD~1       # Undo last commit (keep changes)
git reset --hard HEAD~1       # Undo last commit (discard changes)
```

## Commit Message Format

```
Type: Brief summary (50 chars or less)

Detailed explanation (wrap at 72 chars):
- What changed
- Why it changed
- Any breaking changes or important notes

Fixes #123 (if applicable)
```

**Types:**
- `Fix:` - Bug fixes
- `Feature:` - New features
- `Refactor:` - Code restructuring
- `Security:` - Security patches
- `Docs:` - Documentation
- `Test:` - Tests
- `Chore:` - Maintenance tasks

## Rules

1. ✅ **NEVER commit directly to `main` or `dev`**
2. ✅ **Always work in feature branches**
3. ✅ **Always create PRs for review**
4. ✅ **Write descriptive commit messages**
5. ✅ **Test before creating PR**
6. ✅ **Delete feature branches after merge**
7. ✅ **Keep commits atomic (one logical change per commit)**
8. ✅ **Pull latest changes before starting new work**

## Example Full Workflow

```bash
# 1. Start new feature
git checkout dev
git pull origin dev
git checkout -b feature/add-sms-integration

# 2. Make changes and commit
# ... edit files ...
git add .
git commit -m "Feature: Add Twilio SMS integration

- Added SMS webhook endpoint
- Integrated with agent manager
- Added SMS credentials to settings"

# 3. Push and create PR
git push -u origin feature/add-sms-integration
gh pr create --base dev --title "Feature: Add SMS Integration" --body "Adds Twilio SMS support for text-based customer interactions"

# 4. After PR is merged
git checkout dev
git pull origin dev
git branch -d feature/add-sms-integration  # Delete local branch
```

## Notes

- Feature branches are automatically deleted on GitHub after PR merge
- Use `git branch -d feature-name` to delete local branches
- If you need to update your feature branch with latest dev:
  ```bash
  git checkout feature/your-feature
  git merge dev
  # or
  git rebase dev
  ```
