run:
	@echo "Running backend..."
	python -m venv venv
	# Activate venv and install dependencies
	# For Linux/macOS:
	. venv/bin/activate && pip install -r requirements.txt
	uvicorn app.main:app --reload --port 3001
