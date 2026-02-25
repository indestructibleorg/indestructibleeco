#!/bin/bash
# Enterprise-grade integration test runner script
# MachineNativeOps - End-to-End Integration Tests

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

# Test types
TEST_TYPES=("smoke" "functional" "performance" "security" "reliability" "user_journey")

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
    
    # Check Docker
    if command -v docker &> /dev/null; then
        print_success "Docker is available"
    else
        print_warning "Docker is not installed. Tests requiring containers will be skipped."
    fi
    
    # Check Redis connection
    if command -v redis-cli &> /dev/null; then
        if redis-cli -h localhost -p 6379 ping &> /dev/null; then
            print_success "Redis connection: OK"
        else
            print_warning "Redis connection: FAILED. Make sure Redis is running."
        fi
    else
        print_warning "redis-cli is not installed"
    fi
}

# Install test dependencies
install_dependencies() {
    print_header "Installing Test Dependencies"
    
    if [ -f "$TEST_DIR/requirements-test.txt" ]; then
        print_info "Installing from requirements-test.txt..."
        pip3 install -q -r "$TEST_DIR/requirements-test.txt"
        print_success "Dependencies installed"
    else
        print_error "requirements-test.txt not found"
        exit 1
    fi
}

# Start test environment
start_test_environment() {
    print_header "Starting Test Environment"
    
    if [ -f "$TEST_DIR/docker-compose.test.yml" ]; then
        print_info "Starting Docker containers..."
        docker-compose -f "$TEST_DIR/docker-compose.test.yml" up -d
        
        # Wait for services to be ready
        print_info "Waiting for services to be ready..."
        sleep 10
        
        print_success "Test environment started"
    else
        print_warning "docker-compose.test.yml not found"
    fi
}

# Stop test environment
stop_test_environment() {
    print_header "Stopping Test Environment"
    
    if [ -f "$TEST_DIR/docker-compose.test.yml" ]; then
        print_info "Stopping Docker containers..."
        docker-compose -f "$TEST_DIR/docker-compose.test.yml" down
        print_success "Test environment stopped"
    fi
}

# Run all tests
run_all_tests() {
    print_header "Running All Tests"
    
    cd "$TEST_DIR"
    
    # Run pytest with all markers
    pytest -v \
        --html="$REPORT_DIR/pytest_report.html" \
        --cov-report=html:"$REPORT_DIR/coverage" \
        --cov-report=xml:"$REPORT_DIR/coverage.xml" \
        --cov-report=term \
        --log-file="$LOG_DIR/pytest.log" \
        | tee "$LOG_DIR/test_run.log"
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_success "All tests passed"
    else
        print_error "Some tests failed"
    fi
    
    return $exit_code
}

# Run specific test type
run_test_type() {
    local test_type=$1
    
    print_header "Running $test_type Tests"
    
    cd "$TEST_DIR"
    
    pytest -v \
        -m "$test_type" \
        --html="$REPORT_DIR/${test_type}_report.html" \
        --cov-report=html:"$REPORT_DIR/${test_type}_coverage" \
        --cov-report=term \
        --log-file="$LOG_DIR/${test_type}.log" \
        | tee "$LOG_DIR/${test_type}_run.log"
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_success "$test_type tests passed"
    else
        print_error "$test_type tests failed"
    fi
    
    return $exit_code
}

# Run smoke tests only
run_smoke_tests() {
    run_test_type "smoke"
}

# Run functional tests
run_functional_tests() {
    run_test_type "functional"
}

# Run performance tests
run_performance_tests() {
    run_test_type "performance"
}

# Run security tests
run_security_tests() {
    run_test_type "security"
}

# Run reliability tests
run_reliability_tests() {
    run_test_type "reliability"
}

# Run user journey tests
run_user_journey_tests() {
    run_test_type "user_journey"
}

# Generate test report
generate_report() {
    print_header "Generating Test Report"
    
    cd "$TEST_DIR"
    
    # Generate coverage report
    if [ -d "$REPORT_DIR/coverage" ]; then
        print_info "Coverage report: $REPORT_DIR/coverage/index.html"
    fi
    
    # Generate HTML report
    if [ -f "$REPORT_DIR/pytest_report.html" ]; then
        print_info "HTML report: $REPORT_DIR/pytest_report.html"
    fi
    
    # Generate summary
    cat > "$REPORT_DIR/test_summary.txt" << EOF
Integration Test Summary
========================

Test Date: $(date)
Test Directory: $TEST_DIR

Output Files:
- HTML Report: $REPORT_DIR/pytest_report.html
- Coverage Report: $REPORT_DIR/coverage/index.html
- Test Log: $LOG_DIR/pytest.log
- Test Run Log: $LOG_DIR/test_run.log

For detailed results, see the HTML report.
EOF
    
    print_success "Test report generated"
}

# Main function
main() {
    print_header "MachineNativeOps Integration Tests"
    print_info "Project Root: $PROJECT_ROOT"
    print_info "Test Directory: $TEST_DIR"
    echo ""
    
    # Parse arguments
    case "${1:-all}" in
        all)
            create_directories
            check_prerequisites
            install_dependencies
            start_test_environment
            run_all_tests
            generate_report
            stop_test_environment
            ;;
        smoke)
            create_directories
            check_prerequisites
            install_dependencies
            start_test_environment
            run_smoke_tests
            generate_report
            stop_test_environment
            ;;
        functional)
            create_directories
            check_prerequisites
            install_dependencies
            start_test_environment
            run_functional_tests
            generate_report
            stop_test_environment
            ;;
        performance)
            create_directories
            check_prerequisites
            install_dependencies
            start_test_environment
            run_performance_tests
            generate_report
            stop_test_environment
            ;;
        security)
            create_directories
            check_prerequisites
            install_dependencies
            start_test_environment
            run_security_tests
            generate_report
            stop_test_environment
            ;;
        reliability)
            create_directories
            check_prerequisites
            install_dependencies
            start_test_environment
            run_reliability_tests
            generate_report
            stop_test_environment
            ;;
        user_journey)
            create_directories
            check_prerequisites
            install_dependencies
            start_test_environment
            run_user_journey_tests
            generate_report
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
            echo "Usage: $0 [all|smoke|functional|performance|security|reliability|user_journey|env-only]"
            echo ""
            echo "Options:"
            echo "  all           - Run all tests (default)"
            echo "  smoke         - Run smoke tests only"
            echo "  functional    - Run functional tests only"
            echo "  performance   - Run performance tests only"
            echo "  security      - Run security tests only"
            echo "  reliability   - Run reliability tests only"
            echo "  user_journey  - Run user journey tests only"
            echo "  env-only      - Start test environment only"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"