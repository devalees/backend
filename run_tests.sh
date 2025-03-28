#!/bin/bash

# Function to display help message
show_help() {
    echo "Usage: ./run_tests.sh [options]"
    echo "Options:"
    echo "  -a, --all         Run all tests"
    echo "  -v, --verbose     Run tests with verbose output"
    echo "  -x, --failfast    Stop on first failure"
    echo "  -k PATTERN        Only run tests matching the pattern"
    echo "  -m MARKER         Only run tests with specific marker"
    echo "  -h, --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run_tests.sh -a -v        # Run all tests verbosely"
    echo "  ./run_tests.sh -k users     # Run only user-related tests"
    echo "  ./run_tests.sh -m views     # Run only view tests"
}

# Default options
PYTEST_ARGS=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -a|--all)
            PYTEST_ARGS="Apps/*/tests/test_*.py"
            shift
            ;;
        -v|--verbose)
            PYTEST_ARGS="$PYTEST_ARGS -v"
            shift
            ;;
        -x|--failfast)
            PYTEST_ARGS="$PYTEST_ARGS -x"
            shift
            ;;
        -k)
            PYTEST_ARGS="$PYTEST_ARGS -k $2"
            shift 2
            ;;
        -m)
            PYTEST_ARGS="$PYTEST_ARGS -m $2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# If no arguments provided, run all tests
if [ -z "$PYTEST_ARGS" ]; then
    PYTEST_ARGS="Apps/*/tests/test_*.py"
fi

# Set environment variables
export PYTHONPATH=.
export DJANGO_SETTINGS_MODULE=Apps.core.settings

# Run the tests
echo "Running tests with arguments: $PYTEST_ARGS"
pytest $PYTEST_ARGS 