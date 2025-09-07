# Git Branching Strategy

## Current Branch Structure (as of 2025-08-29)

### Main Branches
- **`main`** - Active development branch (will deploy to staging/dev environment)
- **`production`** - Production releases only (will deploy to production)
- **`dev`** - Legacy development branch (to be deprecated - currently deploys to dev)
- **`master`** - Legacy production branch (to be deprecated - currently deploys to production)

### Supporting Branches
- **`feature/*`** - New features
- **`fix/*`** - Bug fixes  
- **`hotfix/*`** - Emergency production fixes

## Workflow

### Regular Development
1. Create feature branch from `main`
   ```bash
   git checkout -b feature/new-feature main
   ```

2. Develop and test locally
   ```bash
   uv run pytest tests/
   uv run ruff check opennem
   ```

3. Create PR to `main`
   - Triggers CI/CD tests
   - Claude review (if configured)
   - Deploys to dev environment after merge

4. After testing in dev, changes auto-promote to production
   - Automated PR created from `main` to `production`
   - Requires approval before merge
   - Deploys to production after merge

### Hotfixes
1. Create hotfix branch from `production`
   ```bash
   git checkout -b hotfix/critical-fix production
   ```

2. Fix and test
3. Create PR to `production` (bypasses main)
4. After merge, backport to `main`

## Migration Status

### Completed (2025-08-29)
- ✅ Created `main` branch from current `dev` state
- ✅ Created `production` branch from current `dev` state (starting point - all environments in sync)
- ✅ Pushed both branches to remote repository

### Next Steps
1. **Update CI/CD pipelines**:
   - Change dev deployments from `dev` → `main`
   - Change production deployments from `master` → `production`

2. **Update GitHub repository settings**:
   - Set default branch to `main`
   - Update branch protection rules for `main` and `production`

3. **Deprecate old branches** (after CI/CD updates):
   ```bash
   # After confirming deployments work with new branches
   git push origin --delete dev
   git push origin --delete master
   ```

4. **Update team documentation and notify developers**

## Benefits
- Clear separation between environments
- All changes go through PR review
- Automatic promotion reduces manual work
- Hotfix path for emergencies
- Compatible with GitHub Flow tools
