# 🔧 Branch Protection Rules Update Instructions

## 📋 Current Status Check Names

### ✅ Required Checks (Add These):

- `CI / test (pull_request)`
- `Quality Feedback / quality-feedback (3.13) (pull_request)`
- `Quality Feedback / security-feedback (pull_request)`
- `PR Checks / Essential Checks (pull_request)`

### ❌ Deprecated Checks (Remove These):

- `build`
- `e2e`
- `performance`
- `quality`
- `test (3.8)`
- `test (3.9)`
- `test (3.10)`
- `test (3.11)`
- `test (3.12)`

## 🚀 Step-by-Step Update Process

### 1. Navigate to Repository Settings

1. Go to your repository on GitHub
2. Click **Settings** tab
3. Click **Branches** in the left sidebar

### 2. Edit Branch Protection Rule

1. Find your protected branch (usually `main` or `develop`)
2. Click **Edit** on the branch protection rule

### 3. Update Status Checks

1. Scroll to **"Require status checks to pass before merging"**
2. **Remove** all deprecated checks listed above
3. **Add** all required checks listed above
4. Make sure **"Require branches to be up to date"** is checked

### 4. Save Changes

1. Click **Save changes**
2. Test with a new PR to verify everything works

## 🔍 Verification

After updating, your PR should show:

- ✅ All required checks passing
- ❌ No more "pending" checks
- 🚀 Ability to merge when all checks pass

## 🆘 Troubleshooting

If you still see issues:

1. **Clear browser cache** and refresh
2. **Wait 5-10 minutes** for GitHub to update
3. **Create a new PR** to test the changes
4. **Check workflow logs** if any checks are failing

## 📞 Need Help?

If you need assistance:

1. Check the workflow logs in the Actions tab
2. Verify all workflows are running successfully
3. Ensure the status check names match exactly (case-sensitive)
