# Publishing PyVerifactu to PyPI

This guide walks through the process of publishing the `pyverifactu` package to the Python Package Index (PyPI).

## Prerequisites

### 1. Create PyPI Accounts

- **PyPI**: Register at https://pypi.org/account/register/
- **TestPyPI** (recommended for testing): Register at https://test.pypi.org/account/register/

### 2. Generate API Tokens

For secure authentication, use API tokens instead of passwords:

**PyPI (Production)**:
1. Go to https://pypi.org/manage/account/token/
2. Create a new API token with scope "Entire account" (or limit to this project after first upload)
3. Save the token securely (format: `pypi-AgEIcHlwaS5vcmc...`)

**TestPyPI**:
1. Go to https://test.pypi.org/manage/account/token/
2. Create a token for testing uploads
3. Save the token securely

### 3. Configure PyPI Credentials

Store your tokens in `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...YOUR_PYPI_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-AgEIcHlwaS5vcmc...YOUR_TESTPYPI_TOKEN_HERE
```

Set proper permissions:
```bash
chmod 600 ~/.pypirc
```

### 4. Install Build Tools

```bash
pip install --upgrade build twine
```

## Pre-Release Checklist

Before publishing, ensure the package is ready:

- [ ] All tests pass: `pytest`
- [ ] Code is formatted: `black src tests`
- [ ] Linting passes: `ruff check src tests`
- [ ] Type checking passes: `mypy src`
- [ ] Version number updated in `pyproject.toml`
- [ ] CHANGELOG updated with release notes (if applicable)
- [ ] Documentation is up to date
- [ ] `README.md` is accurate and complete
- [ ] All changes committed to git
- [ ] Git tag created for the version

## Update Version Number

Edit `pyproject.toml` and update the version:

```toml
[project]
name = "pyverifactu"
version = "0.1.0"  # Update this
```

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions
- **PATCH** version for backwards-compatible bug fixes

## Building the Package

### 1. Clean Previous Builds

```bash
rm -rf dist/ build/ *.egg-info
```

### 2. Build Distribution Files

```bash
python -m build
```

This creates:
- `dist/pyverifactu-X.Y.Z-py3-none-any.whl` (wheel distribution)
- `dist/pyverifactu-X.Y.Z.tar.gz` (source distribution)

### 3. Verify Build Contents

```bash
# Check wheel contents
unzip -l dist/pyverifactu-*.whl

# Check source distribution
tar -tzf dist/pyverifactu-*.tar.gz
```

Ensure:
- Source files are included (`verifactu/` directory, not `src/verifactu/`)
- No unnecessary files (`.pyc`, `__pycache__`, `.git`, etc.)
- `MANIFEST.in` properly includes/excludes files

## Testing on TestPyPI

Always test on TestPyPI before publishing to production PyPI.

### 1. Upload to TestPyPI

```bash
python -m twine upload --repository testpypi dist/*
```

### 2. Verify Upload

Visit: https://test.pypi.org/project/pyverifactu/

### 3. Test Installation

Create a new virtual environment and install from TestPyPI:

```bash
# Create fresh environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pyverifactu

# Test import
python -c "from verifactu import RegistrationRecord; print('Success!')"

# Run basic tests
python example.py

# Deactivate and cleanup
deactivate
rm -rf test_env
```

Note: `--extra-index-url https://pypi.org/simple/` is needed because dependencies (pydantic, requests, cryptography, etc.) are not on TestPyPI.

## Publishing to PyPI

Once testing is successful:

### 1. Upload to PyPI

```bash
python -m twine upload dist/*
```

### 2. Verify Upload

Visit: https://pypi.org/project/pyverifactu/

### 3. Create Git Tag

```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
git push origin main
```

### 4. Test Installation

```bash
# In a fresh environment
pip install pyverifactu

# Verify
python -c "from verifactu import RegistrationRecord; print('Success!')"
```

## Troubleshooting

### "File already exists" Error

PyPI does not allow re-uploading the same version. Solutions:
- Increment version number in `pyproject.toml`
- Rebuild: `rm -rf dist/ && python -m build`
- Upload new version

### Missing Files in Distribution

Edit `MANIFEST.in` to include additional files:
```
include LICENSE
include README.md
include CLAUDE.md
recursive-include src/verifactu *.py
recursive-include tests *.py
```

Rebuild after changes.

### Import Errors After Installation

Ensure `pyproject.toml` has correct package discovery:
```toml
[tool.setuptools.packages.find]
where = ["src"]
```

The package structure should be `src/verifactu/` (not `src/pyverifactu/`).

### Authentication Failures

- Verify token in `~/.pypirc` is correct
- Ensure no extra whitespace in token
- Check token hasn't expired
- Generate a new token if needed

### SSL Certificate Errors

Update certifi:
```bash
pip install --upgrade certifi
```

## Post-Release

After successful publication:

1. **Announce the Release**:
   - Update project README with installation instructions
   - Create GitHub release with changelog
   - Notify users/contributors

2. **Monitor Issues**:
   - Watch for installation problems
   - Check PyPI download statistics
   - Respond to user feedback

3. **Plan Next Release**:
   - Create milestone for next version
   - Tag issues for next release
   - Update development roadmap

## Automation (Optional)

Consider automating releases with GitHub Actions:

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install build twine
      - name: Build package
        run: python -m build
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

Store your PyPI API token in GitHub repository secrets as `PYPI_API_TOKEN`.

## Quick Reference

```bash
# Complete release workflow
rm -rf dist/ build/ *.egg-info
python -m build
python -m twine upload --repository testpypi dist/*  # Test first
python -m twine upload dist/*                         # Then production
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

## Resources

- **PyPI**: https://pypi.org/
- **TestPyPI**: https://test.pypi.org/
- **Python Packaging Guide**: https://packaging.python.org/
- **Twine Documentation**: https://twine.readthedocs.io/
- **Semantic Versioning**: https://semver.org/
