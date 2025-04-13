#!/bin/bash
# Script to run tests and check coverage for the filtering system

# Set environment variables
export DJANGO_SETTINGS_MODULE=core.settings

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}===== Testing Filtering and Aggregation System =====${NC}"

# Run tests with coverage
echo -e "\n${YELLOW}Running tests with coverage...${NC}"
pytest Apps/filtering/tests/ -v --cov=Apps.filtering --cov-report=term --cov-report=html

# Check coverage threshold
COVERAGE=$(coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//')

echo -e "\n${YELLOW}Coverage: ${COVERAGE}%${NC}"

if (( $(echo "$COVERAGE < 90" | bc -l) )); then
    echo -e "${RED}Coverage is below 90%. Please add more tests.${NC}"
    exit 1
else
    echo -e "${GREEN}Coverage is above 90%. Good job!${NC}"
fi

echo -e "\n${YELLOW}===== Tests Completed =====${NC}"

# Check for linting errors
echo -e "\n${YELLOW}Checking for linting errors...${NC}"
flake8 Apps/filtering/ --exclude=__pycache__,migrations --max-line-length=100

echo -e "\n${GREEN}All checks completed successfully!${NC}" 