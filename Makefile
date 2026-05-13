.PHONY: install dev clean lint typecheck test run

# Install production dependencies
install:
	uv sync --group prod

# Install all dependencies including dev
dev:
	uv sync --group dev

# Clean temporary and export files
clean:
	rm -rf temp/*
	rm -rf exports/*
	rm -rf .coverage htmlcov
	rm -rf .mypy_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Lint with ruff
lint:
	ruff check app/ tests/
	ruff format --check app/ tests/

# Format with ruff
format:
	ruff check --fix app/ tests/
	ruff format app/ tests/

# Type check with mypy
typecheck:
	mypy app/

# Run tests
test:
	pytest tests/ -v --cov=app/ --cov-report=term-missing

# Run the CLI
run:
	python main.py

# Build Docker image
docker-build:
	docker build -t yt-clipper .

# Docker compose
docker-up:
	docker compose up

# Create project structure
scaffold:
	mkdir -p app/{cli,core,config,domain,schemas,services/{youtube,transcript,ai,ffmpeg,subtitles,scoring,reframing,export},workflows,infrastructure/{logging,storage,subprocess,cache},utils,temp,exports,tests}
	touch app/__init__.py
	find app -type d -exec touch {}/__init__.py \;
	touch temp/.gitkeep exports/.gitkeep

# Pre-commit setup
pre-commit:
	pre-commit install
