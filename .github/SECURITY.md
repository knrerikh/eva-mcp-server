# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability within Eva MCP Server, please send an email to the maintainers. All security vulnerabilities will be promptly addressed.

**Please do not report security vulnerabilities through public GitHub issues.**

### What to Include

When reporting a vulnerability, please include:

1. **Description**: A clear description of the vulnerability
2. **Impact**: What an attacker could achieve by exploiting this vulnerability
3. **Steps to Reproduce**: Detailed steps to reproduce the vulnerability
4. **Affected Versions**: Which versions of the software are affected
5. **Suggested Fix**: If you have ideas on how to fix it (optional)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - Critical: Within 7 days
  - High: Within 14 days
  - Medium: Within 30 days
  - Low: Next release cycle

## Security Best Practices

When using Eva MCP Server:

1. **API Tokens**: 
   - Never commit API tokens to version control
   - Use environment variables for sensitive data
   - Rotate tokens regularly
   - Use read-only mode when possible

2. **Network Security**:
   - Use HTTPS for API connections
   - Verify SSL certificates
   - Use secure network connections

3. **Access Control**:
   - Limit who has access to API tokens
   - Use principle of least privilege
   - Monitor API usage

4. **Updates**:
   - Keep Eva MCP Server updated
   - Monitor security advisories
   - Review changelogs for security fixes

## Known Security Considerations

### Read-Only Mode

By default, the server runs in read-only mode to prevent accidental modifications. This is a security feature that should be kept enabled unless write operations are explicitly needed.

### API Token Storage

API tokens are stored in environment variables or `.env` files. Ensure these files are:
- Not committed to version control (`.env` is in `.gitignore`)
- Have appropriate file permissions
- Are not shared publicly

### Network Exposure

The MCP server communicates over stdio and should not be directly exposed to the network. If you need network access, use appropriate security measures like:
- VPN
- SSH tunneling
- Proper authentication and authorization

## Disclosure Policy

When we receive a security bug report, we will:

1. Confirm the problem and determine affected versions
2. Audit code to find similar problems
3. Prepare fixes for all supported versions
4. Release patches as soon as possible

We appreciate your efforts to responsibly disclose your findings and will make every effort to acknowledge your contributions.

