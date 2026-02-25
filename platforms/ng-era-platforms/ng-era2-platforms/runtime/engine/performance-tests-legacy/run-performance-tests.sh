#!/bin/bash
# Enterprise-grade performance testing runner script
# MachineNativeOps - Performance Benchmarking

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEST_DIR="$SCRIPT_DIR"
OUTPUT_DIR="$TEST_DIR/output"
LOG_DIR="$OUTPUT_DIR/logs"
REPORT_DIR="$OUTPUT_DIR/reports"
BENCHMARK_DIR="$OUTPUT_DIR/benchmarks"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Create output directories
create_directories() {
    mkdir -p "$OUTPUT_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$REPORT_DIR"
    mkdir -p "$BENCHMARK_DIR"
    print_success "Created output directories"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python version: $PYTHON_VERSION"
    else
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check pip
    if command -v pip3 &> /dev/null; then
        print_success "pip is available"
    else
        print_error "pip is not installed"
        exit 1
    fi
}

# Install test dependencies
install_dependencies() {
    print_header "Installing Test Dependencies"
    
    if [ -f "$TEST_DIR/requirements-performance.txt" ]; then
        print_info "Installing from requirements-performance.txt..."
        pip3 install -q -r "$TEST_DIR/requirements-performance.txt"
        print_success "Dependencies installed"
    else
        print_error "requirements-performance.txt not found"
        exit 1
    fi
}

# Start test environment
start_test_environment() {
    print_header "Starting Test Environment"
    
    if [ -f "$TEST_DIR/docker-compose.performance.yml" ]; then
        print_info "Starting Docker containers..."
        docker-compose -f "$TEST_DIR/docker-compose.performance.yml" up -d
        
        # Wait for services to be ready
        print_info "Waiting for services to be ready..."
        sleep 10
        
        print_success "Test environment started"
    else
        print_warning "docker-compose.performance.yml not found"
    fi
}

# Stop test environment
stop_test_environment() {
    print_header "Stopping Test Environment"
    
    if [ -f "$TEST_DIR/docker-compose.performance.yml" ]; then
        print_info "Stopping Docker containers..."
        docker-compose -f "$TEST_DIR/docker-compose.performance.yml" down
        print_success "Test environment stopped"
    fi
}

# Run all performance tests
run_all_tests() {
    print_header "Running All Performance Tests"
    
    cd "$TEST_DIR"
    
    pytest -v \
        -m "performance" \
        --html="$REPORT_DIR/performance_report.html" \
        --self-contained-html \
        --cov-report=html:"$REPORT_DIR/coverage" \
        --cov-report=term \
        --log-file="$LOG_DIR/performance.log" \
        | tee "$LOG_DIR/test_run.log"
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_success "All performance tests passed"
    else
        print_error "Some performance tests failed"
    fi
    
    return $exit_code
}

# Main function
main() {
    print_header "MachineNativeOps Performance Testing"
    print_info "Project Root: $PROJECT_ROOT"
    print_info "Test Directory: $TEST_DIR"
    echo ""
    
    case "${1:-all}" in
        all)
            create_directories
            check_prerequisites
            install_dependencies
            start_test_environment
            run_all_tests
            stop_test_environment
            ;;
        env-only)
            create_directories
            start_test_environment
            print_info "Test environment started. Press Ctrl+C to stop."
            trap stop_test_environment EXIT
            sleep infinity
            ;;
        *)
            echo "Usage: $0 [all|env-only]"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"