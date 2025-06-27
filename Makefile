# Target to install dependencies and setup the environment
install:
	bash install.sh

# Target to run the FastAPI application
run:
	# Add poetry to the PATH
	export PATH=$$HOME/.local/bin:$$PATH && \
	poetry run uvicorn app.main:app --reload