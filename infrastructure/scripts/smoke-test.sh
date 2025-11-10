#!/bin/bash

# ============================================================================
# DeepAgents Control Platform - Smoke Test Script
# ============================================================================
# This script runs basic smoke tests after deployment
# It verifies that all critical functionality is working

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${1:-production}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRASTRUCTURE_DIR="$(dirname "$SCRIPT_DIR")"

# Determine API base URL based on environment
case "$ENVIRONMENT" in
    "production")
        API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
        ;;
    "staging")
        API_BASE_URL="${API_BASE_URL:-http://localhost:8080}"
        ;;
    *)
        log_error "Unknown environment: $ENVIRONMENT"
        exit 1
        ;;
esac

# Test results
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

test_pass() {
    TESTS_PASSED=$((TESTS_PASSED + 1))
    log_success "PASS: $1"
}

test_fail() {
    TESTS_FAILED=$((TESTS_FAILED + 1))
    FAILED_TESTS+=("$1")
    log_error "FAIL: $1"
}

run_test() {
    TESTS_RUN=$((TESTS_RUN + 1))
    log_info "Running: $1"
}

# ============================================================================
# Smoke Tests
# ============================================================================

log_info "Starting smoke tests for $ENVIRONMENT environment..."
log_info "API Base URL: $API_BASE_URL"
echo ""

# ============================================================================
# Test 1: Health Check Endpoint
# ============================================================================

run_test "Health check endpoint"
if curl -f -s "$API_BASE_URL/health" > /dev/null; then
    HEALTH_STATUS=$(curl -s "$API_BASE_URL/health" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    if [ "$HEALTH_STATUS" = "healthy" ]; then
        test_pass "Health check endpoint returns healthy status"
    else
        test_fail "Health check endpoint returned status: $HEALTH_STATUS"
    fi
else
    test_fail "Health check endpoint not accessible"
fi

# ============================================================================
# Test 2: API Documentation
# ============================================================================

run_test "API documentation endpoint"
if curl -f -s "$API_BASE_URL/docs" > /dev/null; then
    test_pass "API documentation is accessible"
else
    test_fail "API documentation not accessible"
fi

# ============================================================================
# Test 3: OpenAPI Schema
# ============================================================================

run_test "OpenAPI schema endpoint"
if curl -f -s "$API_BASE_URL/openapi.json" > /dev/null; then
    test_pass "OpenAPI schema is accessible"
else
    test_fail "OpenAPI schema not accessible"
fi

# ============================================================================
# Test 4: Metrics Endpoint
# ============================================================================

run_test "Prometheus metrics endpoint"
if curl -f -s "$API_BASE_URL/api/v1/metrics" > /dev/null; then
    # Check if metrics are in Prometheus format
    if curl -s "$API_BASE_URL/api/v1/metrics" | grep -q "^# HELP"; then
        test_pass "Metrics endpoint returns Prometheus format"
    else
        test_fail "Metrics endpoint not in Prometheus format"
    fi
else
    test_fail "Metrics endpoint not accessible"
fi

# ============================================================================
# Test 5: Readiness Check
# ============================================================================

run_test "Readiness check endpoint"
if curl -f -s "$API_BASE_URL/api/v1/health/readiness" > /dev/null; then
    READY_STATUS=$(curl -s "$API_BASE_URL/api/v1/health/readiness" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    if [ "$READY_STATUS" = "ready" ]; then
        test_pass "Service is ready to serve traffic"
    else
        test_fail "Service readiness check failed: $READY_STATUS"
    fi
else
    test_fail "Readiness check endpoint not accessible"
fi

# ============================================================================
# Test 6: Deep Health Check
# ============================================================================

run_test "Deep health check"
DEEP_HEALTH_RESPONSE=$(curl -s "$API_BASE_URL/api/v1/health/deep")

# Check database health
DB_STATUS=$(echo "$DEEP_HEALTH_RESPONSE" | grep -o '"database":{"status":"[^"]*"' | cut -d'"' -f6)
if [ "$DB_STATUS" = "healthy" ]; then
    test_pass "Database is healthy"
else
    test_fail "Database health check failed: $DB_STATUS"
fi

# Check Redis health
REDIS_STATUS=$(echo "$DEEP_HEALTH_RESPONSE" | grep -o '"redis":{"status":"[^"]*"' | cut -d'"' -f6)
if [ "$REDIS_STATUS" = "healthy" ]; then
    test_pass "Redis is healthy"
else
    test_fail "Redis health check failed: $REDIS_STATUS"
fi

# ============================================================================
# Test 7: List Agents Endpoint
# ============================================================================

run_test "List agents endpoint"
if curl -f -s "$API_BASE_URL/api/v1/agents" > /dev/null; then
    # Check if response is valid JSON array
    if curl -s "$API_BASE_URL/api/v1/agents" | grep -q '^\['; then
        test_pass "Agents endpoint returns valid JSON"
    else
        test_fail "Agents endpoint response is not valid JSON"
    fi
else
    test_fail "Agents endpoint not accessible"
fi

# ============================================================================
# Test 8: List Tools Endpoint
# ============================================================================

run_test "List tools endpoint"
if curl -f -s "$API_BASE_URL/api/v1/tools" > /dev/null; then
    test_pass "Tools endpoint is accessible"
else
    test_fail "Tools endpoint not accessible"
fi

# ============================================================================
# Test 9: List Templates Endpoint
# ============================================================================

run_test "List templates endpoint"
if curl -f -s "$API_BASE_URL/api/v1/templates" > /dev/null; then
    test_pass "Templates endpoint is accessible"
else
    test_fail "Templates endpoint not accessible"
fi

# ============================================================================
# Test 10: Monitoring Endpoint
# ============================================================================

run_test "Monitoring stats endpoint"
if curl -f -s "$API_BASE_URL/api/v1/monitoring/stats" > /dev/null; then
    test_pass "Monitoring stats endpoint is accessible"
else
    test_fail "Monitoring stats endpoint not accessible"
fi

# ============================================================================
# Test 11: Database Connection
# ============================================================================

run_test "Database connectivity"
# This is checked via deep health check, but we can verify it's working
if [ "$DB_STATUS" = "healthy" ]; then
    test_pass "Database connection is working"
else
    test_fail "Database connection issues detected"
fi

# ============================================================================
# Test 12: Redis Connection
# ============================================================================

run_test "Redis connectivity"
# This is checked via deep health check
if [ "$REDIS_STATUS" = "healthy" ]; then
    test_pass "Redis connection is working"
else
    test_fail "Redis connection issues detected"
fi

# ============================================================================
# Test 13: Response Time Check
# ============================================================================

run_test "API response time check"
RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}\n' "$API_BASE_URL/health")
RESPONSE_TIME_MS=$(echo "$RESPONSE_TIME * 1000" | bc)

if (( $(echo "$RESPONSE_TIME < 1.0" | bc -l) )); then
    test_pass "API response time is good (${RESPONSE_TIME_MS}ms)"
else
    test_warning "API response time is slow (${RESPONSE_TIME_MS}ms)"
    test_pass "API is responding (but slowly)"
fi

# ============================================================================
# Test 14: CORS Headers (if applicable)
# ============================================================================

run_test "CORS headers check"
CORS_HEADER=$(curl -s -I "$API_BASE_URL/health" | grep -i "access-control-allow-origin")
if [ -n "$CORS_HEADER" ]; then
    test_pass "CORS headers are configured"
else
    test_warning "CORS headers not found (may be expected)"
    test_pass "CORS check completed"
fi

# ============================================================================
# Optional: External Monitoring Check
# ============================================================================

if [ -n "${PROMETHEUS_URL:-}" ]; then
    run_test "Prometheus connectivity"
    if curl -f -s "$PROMETHEUS_URL/api/v1/status/config" > /dev/null; then
        test_pass "Prometheus is accessible"
    else
        test_fail "Prometheus is not accessible"
    fi
fi

if [ -n "${GRAFANA_URL:-}" ]; then
    run_test "Grafana connectivity"
    if curl -f -s "$GRAFANA_URL/api/health" > /dev/null; then
        test_pass "Grafana is accessible"
    else
        test_fail "Grafana is not accessible"
    fi
fi

# ============================================================================
# Test Summary
# ============================================================================

echo ""
echo "============================================"
echo "Smoke Test Summary"
echo "============================================"
echo "Environment: $ENVIRONMENT"
echo "Tests Run: $TESTS_RUN"
echo "Tests Passed: $TESTS_PASSED"
echo "Tests Failed: $TESTS_FAILED"
echo "Success Rate: $(( (TESTS_PASSED * 100) / TESTS_RUN ))%"
echo "============================================"

if [ $TESTS_FAILED -gt 0 ]; then
    echo "Failed Tests:"
    for test in "${FAILED_TESTS[@]}"; do
        echo "  - $test"
    done
    echo "============================================"
    log_error "Smoke tests failed!"
    exit 1
else
    log_success "All smoke tests passed!"
    exit 0
fi
