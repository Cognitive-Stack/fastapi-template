# Target to install dependencies and setup the environment
install:
	bash install.sh

# Target to run the FastAPI application
run:
	uv run uvicorn app.main:app --reload