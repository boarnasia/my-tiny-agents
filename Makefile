# Makefile

.PHONY: install run-agent clean help

# Virtual environment setup
VENV_DIR = .venv
VENV_PYTHON = $(VENV_DIR)/bin/python3
VENV_PIP = $(VENV_DIR)/bin/pip

# Default server paths and model
SERVER_PATHS ?= servers/github_trends_server.py servers/command_executor_server.py servers/web_search_server.py servers/python_executor_server.py servers/task_manager_server.py
MODEL_NAME ?= gemini/gemini-2.0-flash-exp

# Setup virtual environment and install dependencies
install:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv $(VENV_DIR); \
	fi
	@echo "Installing dependencies..."
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install .

# Run the agent (main command)
#run-agent: install
run-agent:
	@echo "Starting Tiny Agent with model: $(MODEL_NAME)"
	$(VENV_PYTHON) -m tiny_agents $(SERVER_PATHS) --model $(MODEL_NAME)

# Clean up
clean:
	@echo "Cleaning up..."
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -exec rm -rf {} +
	rm -rf $(VENV_DIR)

# Show help
help:
	@echo "Available commands:"
	@echo "  make run-agent    - Start the agent (default: all servers)"
	@echo "  make install      - Install dependencies"
	@echo "  make clean        - Clean up files and virtual environment"
	@echo ""
	@echo "Examples:"
	@echo "  make run-agent"
	@echo "  make run-agent SERVER_PATHS=\"servers/github_trends_server.py\""
	@echo "  make run-agent MODEL_NAME=\"anthropic/claude-3-5-sonnet-20241022\"" 