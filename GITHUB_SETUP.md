# GitHub Setup Guide

This guide explains how to publish the Eva MCP Server project to GitHub.

## Prerequisites

- Git installed on your system
- GitHub account
- Repository already initialized locally (done)

## Step 1: Create GitHub Repository

1. Go to [GitHub](https://github.com)
2. Click the "+" icon in the top right corner
3. Select "New repository"
4. Fill in the details:
   - **Repository name**: `eva-mcp-server`
   - **Description**: `MCP server for Eva-project API integration`
   - **Visibility**: Choose Public or Private
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
5. Click "Create repository"

## Step 2: Add Remote and Push

After creating the repository, GitHub will show you commands. Use these:

```bash
# Add the remote repository
git remote add origin https://github.com/YOUR_USERNAME/eva-mcp-server.git

# Push to GitHub
git push -u origin master
```

Replace `YOUR_USERNAME` with your GitHub username.

## Step 3: Configure Repository Settings

### Branch Protection

1. Go to repository Settings → Branches
2. Add branch protection rule for `master`:
   - Require pull request reviews before merging
   - Require status checks to pass before merging
   - Select: `CI`, `lint`
   - Require branches to be up to date before merging

### Secrets Configuration

For CI/CD to work properly, add these secrets:

1. Go to Settings → Secrets and variables → Actions
2. Add the following secrets:
   - `PYPI_API_TOKEN`: Your PyPI API token (for publishing packages)
   - `CODECOV_TOKEN`: Your Codecov token (for coverage reports)

### Topics/Tags

Add relevant topics to make your repository discoverable:

1. Go to repository main page
2. Click the gear icon next to "About"
3. Add topics:
   - `mcp`
   - `eva-project`
   - `api-client`
   - `python`
   - `cursor`
   - `claude`
   - `ai-assistant`
   - `model-context-protocol`

## Step 4: Create Initial Release

1. Go to Releases → Create a new release
2. Click "Choose a tag" and type `v0.1.0`
3. Set release title: `v0.1.0 - Initial Release`
4. Add release notes from CHANGELOG.md
5. Click "Publish release"

This will trigger the publish workflow to PyPI (if configured).

## Step 5: Enable GitHub Features

### GitHub Pages (Optional)

If you want to host documentation:

1. Go to Settings → Pages
2. Source: Deploy from a branch
3. Branch: `master` / `docs` folder
4. Save

### Discussions (Optional)

Enable Discussions for community engagement:

1. Go to Settings → Features
2. Check "Discussions"

### Projects (Optional)

Create a project board for task management:

1. Go to Projects tab
2. Create a new project
3. Choose a template or start from scratch

## Step 6: Update Repository Description

1. Go to repository main page
2. Click the gear icon next to "About"
3. Add:
   - **Description**: `MCP server for Eva-project API integration. Enables AI assistants like Claude and Cursor to interact with Eva tasks, projects, and documents.`
   - **Website**: Your documentation URL (if any)
   - **Topics**: (as mentioned above)

## Step 7: Set Up Integrations (Optional)

### Codecov

1. Go to [Codecov.io](https://codecov.io)
2. Sign in with GitHub
3. Add your repository
4. Copy the token and add it to GitHub Secrets

### Dependabot

Dependabot is already configured via `.github/dependabot.yml`. It will:
- Automatically check for dependency updates
- Create PRs for updates
- Run weekly

## Verification Checklist

After setup, verify:

- [ ] Repository is accessible
- [ ] README displays correctly with badges
- [ ] CI workflow runs on push
- [ ] Issues and PRs use templates
- [ ] Branch protection is enabled
- [ ] Secrets are configured
- [ ] Topics/tags are added
- [ ] License is visible
- [ ] Contributing guidelines are accessible

## Maintenance

### Regular Tasks

1. **Review Dependabot PRs**: Weekly
2. **Update CHANGELOG**: Before each release
3. **Tag releases**: Follow semantic versioning
4. **Monitor CI**: Check for failing builds
5. **Review issues**: Respond to community feedback

### Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Commit changes
4. Create and push tag:
   ```bash
   git tag -a v0.x.x -m "Release v0.x.x"
   git push origin v0.x.x
   ```
5. Create GitHub release
6. Verify PyPI publication

## Troubleshooting

### Push Rejected

If push is rejected:
```bash
git pull --rebase origin master
git push origin master
```

### CI Failing

1. Check workflow logs in Actions tab
2. Verify all dependencies are in requirements.txt
3. Ensure tests pass locally
4. Check Python version compatibility

### Badge Not Showing

1. Verify workflow name matches badge URL
2. Wait a few minutes for GitHub to update
3. Check workflow has run at least once

## Additional Resources

- [GitHub Docs](https://docs.github.com)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Semantic Versioning](https://semver.org)
- [Keep a Changelog](https://keepachangelog.com)
- [MCP Documentation](https://modelcontextprotocol.io)

## Support

For issues with this setup guide, please open an issue on GitHub.

