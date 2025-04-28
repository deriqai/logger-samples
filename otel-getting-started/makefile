# Makefile

# Declare targets that are not files
.PHONY: help bootstrap rolldice-nootel rolldice-otel rolldice-tracer

# Default target (optional, often set to 'help' or 'all')
default: help

help:
	@echo "" # Use echo for blank line (cross-platform)
	@echo "-----------------------------------" # Fixed extra quote
	@echo ""
	@echo "Available commands:"
	@echo "  make bootstrap        - Install dependencies"
	@echo "  make rolldice-otel    - Run Flask app with OpenTelemetry instrumentation"
	@echo "  make rolldice-tracer  - Run Flask app with OpenTelemetry tracer"	
	@echo "  make rolldice-nootel  - Run Flask app without instrumentation"
	@echo "  make help             - Show this help message"
	@echo ""

bootstrap:
	@echo ""
	@echo "Setting up dependencies..."
	@echo "Consider running this inside a virtual environment."
	@echo ""
	# Use python -m pip for potentially better interpreter association
	python -m pip install flask opentelemetry-distro
	# Ensure opentelemetry-bootstrap is run after installation
	opentelemetry-bootstrap -a install
	@echo ""
	@echo "Bootstrap complete."

rolldice-nootel:
	@echo ""
	@echo "Running /rolldice app without OpenTelemetry instrumentation..."
	@echo "Access at http://localhost:8080/rolldice"
	@echo ""
	# Optionally set FLASK_APP explicitly
	FLASK_APP=app.py flask run --port 8080

rolldice-otel:
	@echo ""
	@echo "Running /rolldice app with OpenTelemetry instrumentation (console exporters)..."
	@echo "Access at http://localhost:8080/rolldice"
	@echo ""
	# Set environment variables on the SAME line as the command that uses them
	OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true \
	FLASK_APP=app.py \
	opentelemetry-instrument \
		--traces_exporter console \
		--metrics_exporter console \
		--logs_exporter console \
		--service_name dice-server \
		flask run --port 8080

rolldice-tracer:
	@echo ""
	@echo "Running /rolldice app with OpenTelemetry tracer (console exporters)..."
	@echo "Access at http://localhost:8080/rolldice"
	@echo ""
	# Set environment variables on the SAME line as the command that uses them
	OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true \
	FLASK_APP=app-with-tracer.py \
	opentelemetry-instrument \
		--traces_exporter console \
		--metrics_exporter console \
		--logs_exporter console \
		--service_name dice-server-tracer \
		flask run --port 8080		

# Example of a clean target (optional)
# .PHONY: clean
# clean:
#	@echo "Cleaning up..."
#	find . -type f -name '*.pyc' -delete
#	find . -type d -name '__pycache__' -exec rm -r {} +

