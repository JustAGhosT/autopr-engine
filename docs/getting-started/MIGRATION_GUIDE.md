# Repository Structure Migration Guide

## 🚀 **What Changed**

The AutoPR Engine repository has undergone a comprehensive structure reorganization to improve
maintainability, reduce clutter, and provide better documentation organization.

## 📁 **Key Changes**

### **Documentation Reorganization**

- **Before**: Plan files scattered at root level (`plan.md`, `plan-phase1-quality-pipeline.md`,
  etc.)
- **After**: All plan files moved to `docs/plans/` directory
- **Impact**: Better organization and easier navigation

### **Build Artifact Cleanup**

- **Removed**: `htmlcov/`, `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`
- **Removed**: `autopr_engine.egg-info/`, `.coverage`, `platform_validation_report.txt`
- **Impact**: Cleaner repository, faster cloning, better .gitignore coverage

### **Documentation Enhancement**

- **Added**: Comprehensive documentation index in `docs/README.md`
- **Added**: Enhanced template system documentation in `templates/README.md`
- **Added**: Repository structure plan in `docs/plans/REPOSITORY_STRUCTURE_PLAN.md`

### **Configuration Cleanup**

- **Removed**: Duplicate `configs/workflows/magic-fix.yaml` (kept `magic_fix.yaml`)
- **Impact**: Eliminated configuration confusion

## 🔄 **Migration Steps**

### **For Developers**

#### **1. Update Import Paths**

If you have any custom scripts that reference the old plan files, update them:

```python
# Old
from pathlib import Path
plan_file = Path("plan.md")

# New
from pathlib import Path
plan_file = Path("docs/plans/plan.md")
```

#### **2. Update Documentation References**

If you have documentation that references the old file locations:

```markdown
# Old

[Quality Pipeline Plan](plan-phase1-quality-pipeline.md)

# New

[Quality Pipeline Plan](docs/plans/plan-phase1-quality-pipeline.md)
```

#### **3. Update CI/CD Scripts**

If you have CI/CD scripts that reference build artifacts:

```bash
# Old (if any scripts referenced these)
coverage_file=".coverage"
htmlcov_dir="htmlcov/"

# New (these are now ignored by .gitignore)
# No changes needed - files are automatically ignored
```

### **For Contributors**

#### **1. Documentation Location**

- **Planning Documents**: Now in `docs/plans/`
- **Architecture Docs**: In `docs/adr/`
- **API Documentation**: In `docs/api/`
- **Getting Started**: In `docs/getting-started/`

#### **2. Template System**

- **Template Documentation**: Enhanced `templates/README.md`
- **Platform Templates**: Organized in `templates/platforms/`
- **Use Case Templates**: In `templates/use-cases/`

#### **3. Configuration Files**

- **Workflow Configs**: In `configs/workflows/`
- **Platform Configs**: In `configs/platforms/`
- **Environment Configs**: In `configs/environments/`

## ✅ **Verification Checklist**

After migration, verify that:

- [ ] All import statements work correctly
- [ ] Documentation links are functional
- [ ] CI/CD pipelines run successfully
- [ ] Local development environment works
- [ ] Template system functions properly
- [ ] Configuration files are accessible

## 🐛 **Troubleshooting**

### **Common Issues**

#### **1. Missing Plan Files**

**Problem**: Scripts can't find plan files **Solution**: Update paths to use `docs/plans/` directory

#### **2. Build Artifacts Reappearing**

**Problem**: Build artifacts are being tracked again **Solution**: The enhanced `.gitignore` should
prevent this. If issues persist, run:

```bash
git rm -r --cached htmlcov/ .mypy_cache/ .ruff_cache/ .pytest_cache/
git add .
git commit -m "Remove build artifacts from tracking"
```

#### **3. Documentation Links Broken**

**Problem**: Internal documentation links don't work **Solution**: Update relative paths to account
for new structure

### **Getting Help**

If you encounter issues during migration:

1. **Check the Documentation**: Review `docs/README.md` for current structure
2. **Review Changes**: See `docs/plans/REPOSITORY_STRUCTURE_PLAN.md` for detailed changes
3. **Open an Issue**: Create a GitHub issue with details about the problem
4. **Contact Maintainers**: Reach out to the development team

## 📊 **Benefits of New Structure**

### **Improved Organization**

- **Clear Separation**: Documentation, code, and configuration are clearly separated
- **Logical Grouping**: Related files are grouped together
- **Easy Navigation**: Intuitive directory structure

### **Better Maintainability**

- **Reduced Clutter**: Root directory is much cleaner
- **Consistent Patterns**: Standardized organization across the project
- **Easier Onboarding**: New contributors can find files quickly

### **Enhanced Documentation**

- **Comprehensive Index**: All documentation is catalogued
- **Better Navigation**: Clear links between related documents
- **Template System**: Well-documented template organization

### **Development Efficiency**

- **Faster Cloning**: Smaller repository without build artifacts
- **Better CI/CD**: Cleaner build processes
- **Reduced Conflicts**: Less chance of merge conflicts from build files

## 🎯 **Next Steps**

After migration:

1. **Explore the New Structure**: Familiarize yourself with the new organization
2. **Update Local Scripts**: Modify any custom scripts to use new paths
3. **Contribute**: Use the new structure for future contributions
4. **Provide Feedback**: Share any suggestions for further improvements

---

**Migration Completed**: August 2025  
**Version**: 1.0.0  
**Status**: ✅ Complete
