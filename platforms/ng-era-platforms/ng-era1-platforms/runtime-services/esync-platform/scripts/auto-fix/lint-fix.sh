#!/bin/bash
set -euo pipefail

echo "🔧 Applying lint and format fixes..."

# Fix Go code
if [ -f "go.mod" ]; then
  echo "Formatting Go code..."
  gofmt -s -w .
  
  echo "Running goimports..."
  goimports -w .
  
  echo "Running golangci-lint..."
  golangci-lint run --fix
fi

# Fix Python code
if [ -f "requirements.txt" ]; then
  echo "Formatting Python code..."
  black .
  isort .
  
  echo "Running flake8..."
  flake8 . --max-line-length=100 --extend-ignore=E203,W503 || true
fi

# Fix Shell scripts
echo "Formatting shell scripts..."
find . -name "*.sh" -exec shfmt -w -i 2 {} \;

echo "✅ Lint and format fixes complete"