# Contributing to Eva MCP Server

Thank you for your interest in the project! We welcome all contributions.

## How to Contribute

### Bug Reports

If you found a bug:

1. Check that the bug hasn't already been reported in Issues
2. Create a new Issue with detailed description:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Python version and dependencies
   - Error logs

### Feature Suggestions

For new feature proposals:

1. Create an Issue with the "enhancement" tag
2. Describe the proposed functionality
3. Explain why it would be useful
4. Provide usage examples

### Pull Requests

1. **Fork the repository**

2. **Create a branch for your changes:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes:**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

4. **Run tests:**
   ```bash
   pytest
   ```

5. **Check code quality:**
   ```bash
   black src/ tests/
   ruff check src/ tests/
   ```

6. **Create a Pull Request:**
   - Describe the changes made
   - Reference related Issues
   - Ensure all tests pass

## Code Style

- We use [Black](https://github.com/psf/black) for formatting
- We use [Ruff](https://github.com/astral-sh/ruff) for linting
- We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Add docstrings for all public functions and classes

## Testing

- Write unit tests for new functionality
- Ensure all existing tests pass
- Aim for test coverage > 80%

## Documentation

- Update README.md when adding new features
- Add usage examples
- Document changes in CHANGELOG.md

## Security

- Never commit tokens or passwords
- Use environment variables for sensitive data
- Report vulnerabilities through Issues with "security" tag

## License

By contributing to the project, you agree that your code will be distributed under the MIT License.

## Questions?

If you have questions, create an Issue with the "question" tag.

Thank you for your contribution! 🎉
