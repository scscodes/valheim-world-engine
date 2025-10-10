# VWE Logging Management Makefile
# Provides convenient commands for log management

.PHONY: help setup monitor rotate cleanup search stats test

# Default target
help:
	@echo "VWE Logging Management Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  setup          - Setup VWE logging system"
	@echo "  setup-dev      - Setup development logging (DEBUG level)"
	@echo "  setup-prod     - Setup production logging (INFO level)"
	@echo ""
	@echo "Monitoring:"
	@echo "  monitor-start  - Start log monitoring"
	@echo "  monitor-stop   - Stop log monitoring"
	@echo "  monitor-status - Show monitoring status"
	@echo "  monitor-health - Show log health status"
	@echo ""
	@echo "Maintenance:"
	@echo "  rotate         - Rotate all log files"
	@echo "  cleanup        - Cleanup old logs (30 days)"
	@echo "  cleanup-force  - Force cleanup of old logs"
	@echo ""
	@echo "Analysis:"
	@echo "  search-error   - Search for errors in logs"
	@echo "  search-warn    - Search for warnings in logs"
	@echo "  stats          - Show log statistics"
	@echo "  stats-detailed - Show detailed log statistics"
	@echo ""
	@echo "Testing:"
	@echo "  test           - Test logging system"
	@echo "  test-generator - Test generator logging"
	@echo "  test-docker    - Test Docker logging"

# Setup commands
setup:
	python3 ../../scripts/manage_logs.py setup --level INFO --format json --output-dir /var/log/vwe

setup-dev:
	python3 ../../scripts/manage_logs.py setup --level DEBUG --format text --output-dir /var/log/vwe

setup-prod:
	python3 ../../scripts/manage_logs.py setup --level INFO --format json --output-dir /var/log/vwe

# Monitoring commands
monitor-start:
	python3 ../../scripts/manage_logs.py monitor --start

monitor-stop:
	python3 ../../scripts/manage_logs.py monitor --stop

monitor-status:
	python3 ../../scripts/manage_logs.py monitor --status

monitor-health:
	python3 ../../scripts/manage_logs.py monitor --health

# Maintenance commands
rotate:
	python3 ../../scripts/manage_logs.py rotate --directory /var/log/vwe

cleanup:
	python3 ../../scripts/manage_logs.py cleanup --directory /var/log/vwe --days 30

cleanup-force:
	python3 ../../scripts/manage_logs.py cleanup --directory /var/log/vwe --days 7

# Analysis commands
search-error:
	python3 ../../scripts/manage_logs.py search "ERROR" --directory /var/log/vwe --hours 24

search-warn:
	python3 ../../scripts/manage_logs.py search "WARN" --directory /var/log/vwe --hours 24

stats:
	python3 ../../scripts/manage_logs.py stats --directory /var/log/vwe

stats-detailed:
	python3 ../../scripts/manage_logs.py stats --directory /var/log/vwe --format json

# Testing commands
test:
	python3 -c "from vwe_logger import main; main()"

test-generator:
	python3 -c "from generator_logging import main; main()"

test-docker:
	python3 -c "from docker_logging import main; main()"

test-rotation:
	python3 -c "from log_rotation import main; main()"

test-monitoring:
	python3 -c "from log_monitoring import main; main()"

# Development commands
dev-setup: setup-dev
	@echo "Development logging setup complete"
	@echo "Logs will be written to /var/log/vwe"
	@echo "Use 'make monitor-start' to begin monitoring"

prod-setup: setup-prod
	@echo "Production logging setup complete"
	@echo "Logs will be written to /var/log/vwe"
	@echo "Use 'make monitor-start' to begin monitoring"

# Quick status check
status: monitor-status stats
	@echo ""
	@echo "Log management status complete"

# Full maintenance cycle
maintenance: rotate cleanup stats
	@echo ""
	@echo "Log maintenance cycle complete"
