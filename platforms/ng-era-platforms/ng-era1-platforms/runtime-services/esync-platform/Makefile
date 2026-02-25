.PHONY: help build test lint clean deps scan validate deploy

help: ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Build
build: ## Build the syncd binary
	@echo "Building syncd..."
	@go build -a -installsuffix cgo -o bin/syncd ./cmd/syncd
	@echo "✅ Build complete"

build-all: ## Build all binaries
	@echo "Building all binaries..."
	@go build -o bin/syncd ./cmd/syncd
	@go build -o bin/scheduler ./cmd/scheduler
	@go build -o bin/worker ./cmd/worker
	@echo "✅ All binaries built"

##@ Test
test: ## Run all tests
	@echo "Running tests..."
	@go test -v -race -coverprofile=coverage.out ./...
	@go tool cover -html=coverage.out -o coverage.html
	@echo "✅ Tests complete"

test-integration: ## Run integration tests
	@echo "Running integration tests..."
	@go test -v -tags=integration ./...
	@echo "✅ Integration tests complete"

##@ Lint
lint: ## Run all linters
	@echo "Running linters..."
	@golangci-lint run --config .config/lint/golangci.yml
	@echo "✅ Linting complete"

lint-fix: ## Fix linting issues
	@echo "Fixing linting issues..."
	@gofmt -s -w .
	@goimports -w .
	@golangci-lint run --fix
	@echo "✅ Linting fixes applied"

##@ Security
scan: ## Run security scans
	@echo "Running security scans..."
	@gitleaks detect --source . --config .gitleaks.toml
	@trivy fs --security-checks vuln,config,secret .
	@echo "✅ Security scans complete"

sca: ## Run software composition analysis
	@echo "Running SCA..."
	@syft . -o spdx-json > artifacts/sbom/spdx.json
	@grype sbom:artifacts/sbom/spdx.json
	@echo "✅ SCA complete"

##@ Validation
validate: ## Validate configurations
	@echo "Validating configurations..."
	@conftest test deploy/ -p .config/conftest/policies/
	@yamllint .config/ deploy/
	@echo "✅ Validation complete"

validate-policies: ## Validate OPA policies
	@echo "Validating OPA policies..."
	@opa test .config/policy/ -v
	@echo "✅ Policy validation complete"

##@ Governance
audit: ## Run governance audit
	@echo "Running governance audit..."
	@bash scripts/naming/discover.sh
	@bash scripts/auto-fix/collect-issues.sh
	@echo "✅ Governance audit complete"

check-naming: ## Check naming conventions
	@echo "Checking naming conventions..."
	@conftest test deploy/ -p .config/conftest/policies/naming_policy.rego
	@echo "✅ Naming check complete"

##@ Deployment
deploy-dev: ## Deploy to dev environment
	@echo "Deploying to dev..."
	@kubectl apply -k deploy/kustomize/overlays/dev/
	@echo "✅ Deployed to dev"

deploy-staging: ## Deploy to staging environment
	@echo "Deploying to staging..."
	@kubectl apply -k deploy/kustomize/overlays/staging/
	@echo "✅ Deployed to staging"

deploy-prod: ## Deploy to production environment
	@echo "Deploying to production..."
	@kubectl apply -k deploy/kustomize/overlays/prod/
	@echo "✅ Deployed to production"

##@ Dependencies
deps: ## Download dependencies
	@echo "Downloading dependencies..."
	@go mod download
	@go mod tidy
	@echo "✅ Dependencies updated"

deps-update: ## Update dependencies
	@echo "Updating dependencies..."
	@go get -u ./...
	@go mod tidy
	@echo "✅ Dependencies updated"

##@ Cleanup
clean: ## Clean build artifacts
	@echo "Cleaning..."
	@rm -rf bin/
	@rm -f coverage.out coverage.html
	@echo "✅ Clean complete"

clean-all: ## Clean all artifacts
	@echo "Deep clean..."
	@rm -rf bin/ artifacts/
	@rm -f coverage.out coverage.html
	@echo "✅ Deep clean complete"

##@ Documentation
docs: ## Generate documentation
	@echo "Generating documentation..."
	@godoc -html ./... > docs/api.html
	@echo "✅ Documentation generated"

##@ CI/CD
ci: lint test validate scan ## Run full CI pipeline
	@echo "✅ CI pipeline complete"

pre-commit: ## Run pre-commit hooks
	@echo "Running pre-commit hooks..."
	@pre-commit run --all-files
	@echo "✅ Pre-commit complete"