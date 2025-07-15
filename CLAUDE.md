# Coverage Collector Development Guide

## Project Overview

This is a GitHub OSS Coverage Collector that analyzes test coverage for popular open source repositories.

## Linting and Code Quality

### Required Tools

The project uses the following linting tools:

1. **flake8** - Python style and error checking
2. **pylint** - Advanced Python static analysis
3. **pylance** - Type checking (VS Code extension)

### Commands to Run

#### Install linting tools

```bash
source venv/bin/activate
pip install pylint flake8
```

#### Run linting before commits

```bash
# Run all linting tools
source venv/bin/activate && flake8 . && pylint *.py && pyright .

# Pylance type checking runs automatically in VS Code
# Config file: pyrightconfig.json
```

#### LGTM (Looks Good To Me) Workflow

When user says "LGTM", run the complete workflow:

```bash
# 1. Run all linting tools
source venv/bin/activate && flake8 . && pylint *.py && pyright .

# 2. Stage all changes
git add .

# 3. Commit with descriptive message
git commit -m "Refactor code and fix linting issues"

# 4. Push to remote
git push
```

#### Fix common issues

- Remove trailing whitespace
- Fix unused variables (prefix with `_` or remove)
- Remove blank lines with whitespace
- Use proper f-string formatting

### Code Quality Standards

- All Python files must pass flake8 without errors
- Pylint score should be above 9.0/10
- Type hints recommended for function parameters and return values
- Import statements should be at the top level when possible

## Testing

```bash
# Test single repository
./run.sh --repo facebook/react

# Test top N repositories
./run.sh 3
```

## Known Issues

- React coverage parsing may be questionable (53% seems low)
- Vue.js and TheAlgorithms/Python repos need better test command detection
- Monorepo support needs improvement for accurate coverage measurement
