# GitHub Configuration

This directory contains GitHub-specific configuration files for the Eva MCP Server project.

## Workflows

### CI Workflow (`workflows/ci.yml`)
Runs on every push and pull request to main/develop branches:
- Tests on Python 3.10, 3.11, and 3.12
- Runs linting with ruff
- Checks code formatting with black
- Runs test suite with pytest
- Uploads coverage reports to Codecov

### Lint Workflow (`workflows/lint.yml`)
Separate linting workflow for quick feedback:
- Runs ruff linter
- Checks black formatting

### Publish Workflow (`workflows/publish.yml`)
Automatically publishes to PyPI when a new release is created:
- Builds the package
- Publishes to PyPI using API token

## Issue Templates

### Bug Report (`ISSUE_TEMPLATE/bug_report.md`)
Template for reporting bugs with structured format including:
- Bug description
- Reproduction steps
- Expected vs actual behavior
- Environment details

### Feature Request (`ISSUE_TEMPLATE/feature_request.md`)
Template for suggesting new features with:
- Problem description
- Proposed solution
- Alternatives considered
- Example usage

## Pull Request Template

Standard template for pull requests including:
- Description and linked issues
- Type of change checklist
- Testing information
- Pre-merge checklist

