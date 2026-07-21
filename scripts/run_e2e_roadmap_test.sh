#!/bin/bash
#
# E2E Test Runner: New User Roadmap Flow
#
# This script:
# 1. Starts the backend API server
# 2. Starts the frontend dev server
# 3. Runs the Playwright E2E test
# 4. Captures screenshot
# 5. Shows results and screenshot path
#
# Usage:
#   ./scripts/run_e2e_roadmap_test.sh
#
# Requirements:
#   - Python venv with dependencies installed
#   - Node.js with npm
#   - Playwright browsers installed (npx playwright install chromium)

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WEB_DIR="$PROJECT_ROOT/web"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  E2E Test: New User Roadmap Flow${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
}
trap cleanup EXIT

# Check if ports are already in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Start backend if not already running
echo -e "${YELLOW}Step 1: Starting backend API server...${NC}"
if check_port 8000; then
    echo -e "  ${GREEN}✓${NC} Backend already running on port 8000"
else
    cd "$PROJECT_ROOT"
    source venv/bin/activate
    uvicorn api:app --port 8000 > /tmp/claire_backend.log 2>&1 &
    BACKEND_PID=$!
    echo -e "  Started backend (PID: $BACKEND_PID)"
    sleep 3

    # Check if backend started successfully
    if ! check_port 8000; then
        echo -e "  ${RED}✗${NC} Backend failed to start. Check /tmp/claire_backend.log"
        cat /tmp/claire_backend.log
        exit 1
    fi
    echo -e "  ${GREEN}✓${NC} Backend running on http://localhost:8000"
fi

# Start frontend if not already running
echo -e "${YELLOW}Step 2: Starting frontend dev server...${NC}"
if check_port 5173; then
    echo -e "  ${GREEN}✓${NC} Frontend already running on port 5173"
else
    cd "$WEB_DIR"
    npm run dev > /tmp/claire_frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo -e "  Started frontend (PID: $FRONTEND_PID)"
    sleep 5

    # Check if frontend started successfully
    if ! check_port 5173; then
        echo -e "  ${RED}✗${NC} Frontend failed to start. Check /tmp/claire_frontend.log"
        cat /tmp/claire_frontend.log
        exit 1
    fi
    echo -e "  ${GREEN}✓${NC} Frontend running on http://localhost:5173"
fi

# Run E2E test
echo -e "${YELLOW}Step 3: Running Playwright E2E test...${NC}"
cd "$WEB_DIR"

# Clear previous test results
rm -f test-results/new-user-cram-roadmap.png

# Run the test
npx playwright test e2e/new-user-roadmap.spec.js --reporter=list 2>&1 | tee /tmp/claire_e2e.log

# Check test result
TEST_EXIT_CODE=${PIPESTATUS[0]}

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  TEST RESULTS${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ ALL E2E TESTS PASSED${NC}"
else
    echo -e "${RED}✗ E2E TESTS FAILED${NC}"
fi

# Show screenshot location
SCREENSHOT="$WEB_DIR/test-results/new-user-cram-roadmap.png"
if [ -f "$SCREENSHOT" ]; then
    echo ""
    echo -e "${GREEN}Screenshot saved:${NC}"
    echo "  $SCREENSHOT"
    echo ""
    echo "Open with:"
    echo "  open $SCREENSHOT"
else
    echo ""
    echo -e "${YELLOW}No screenshot found${NC}"
fi

# Extract key info from logs
echo ""
echo -e "${BLUE}Key Information from Test:${NC}"
grep -E "(Plan Mode|Countdown|Roadmap Block Order|✓|✗)" /tmp/claire_e2e.log | head -30

exit $TEST_EXIT_CODE
