# Quick Guide: Publish to GitHub

This is a quick reference for publishing the Eva MCP Server to GitHub. For detailed instructions, see [GITHUB_SETUP.md](GITHUB_SETUP.md).

## Prerequisites

✅ Git repository initialized (done)
✅ All files committed (done)
✅ GitHub account ready

## Quick Steps

### 1. Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `eva-mcp-server`
3. Description: `MCP server for Eva-project API integration`
4. Choose visibility (Public/Private)
5. **DO NOT** initialize with README, .gitignore, or license
6. Click "Create repository"

### 2. Push to GitHub

```bash
# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/eva-mcp-server.git

# Push code
git push -u origin master
```

### 3. Configure Repository (Optional but Recommended)

#### Add Topics
Settings → About → Add topics:
- `mcp`
- `eva-project`
- `api-client`
- `python`
- `cursor`
- `claude`
- `ai-assistant`

#### Enable Features
Settings → Features:
- ✅ Issues
- ✅ Discussions (optional)
- ✅ Projects (optional)

#### Set Up Secrets (for CI/CD)
Settings → Secrets and variables → Actions:
- `PYPI_API_TOKEN` (for publishing to PyPI)
- `CODECOV_TOKEN` (for code coverage)

#### Branch Protection
Settings → Branches → Add rule for `master`:
- ✅ Require pull request reviews
- ✅ Require status checks (CI, lint)
- ✅ Require branches to be up to date

### 4. Create First Release

1. Go to Releases → Create a new release
2. Tag: `v0.1.0`
3. Title: `v0.1.0 - Initial Release`
4. Copy description from CHANGELOG.md
5. Click "Publish release"

## What's Included

Your repository now has:

✅ **Source Code**: Complete Python package
✅ **Documentation**: README, CONTRIBUTING, CHANGELOG, etc.
✅ **CI/CD**: GitHub Actions workflows
✅ **Templates**: Issue and PR templates
✅ **Security**: Security policy and code of conduct
✅ **Configuration**: .gitignore, .gitattributes, .editorconfig
✅ **Dependencies**: Dependabot configuration

## Next Steps

1. **Update README badges**: Replace `knrerikh` with your username in badge URLs
2. **Configure secrets**: Add PYPI_API_TOKEN and CODECOV_TOKEN
3. **Enable branch protection**: Protect master branch
4. **Create first release**: Tag v0.1.0
5. **Share**: Add repository link to your profile

## Verification

After publishing, check:

- [ ] Repository is accessible
- [ ] README displays correctly
- [ ] CI workflow runs (Actions tab)
- [ ] All badges show correct status
- [ ] Issues use templates
- [ ] License is visible

## Common Commands

```bash
# Check current status
git status

# View commit history
git log --oneline

# Create a new tag
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0

# Update remote
git remote -v
git remote set-url origin NEW_URL
```

## Troubleshooting

**Problem**: Push rejected
```bash
git pull --rebase origin master
git push origin master
```

**Problem**: Wrong remote URL
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/eva-mcp-server.git
```

**Problem**: Need to change commit message
```bash
git commit --amend -m "New message"
git push --force-with-lease origin master
```

## Support

- Detailed guide: [GITHUB_SETUP.md](GITHUB_SETUP.md)
- GitHub Docs: https://docs.github.com
- Issues: Create an issue on GitHub

---

**Ready to publish?** Follow steps 1-2 above to get started! 🚀

