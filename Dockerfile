FROM python:3.12-slim-bookworm

WORKDIR /app

ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"

# Install system dependencies and Poetry
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    apt-get remove -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Copy only dependency files to leverage Docker cache
COPY pyproject.toml poetry.lock* /app/

# Install project dependencies
RUN poetry install --no-root --no-dev

# Copy the rest of the application code
COPY . /app/

# Create directories for logs and data
RUN mkdir -p logs data

# Command to run the bot (will be overridden in docker-compose.yml but good for standalone run)
CMD ["poetry", "run", "python", "main.py"]
