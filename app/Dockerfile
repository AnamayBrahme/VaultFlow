# ── Build stage ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .

# Create a clean, isolated virtual environment and install packages inside it
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ── Final stage ──────────────────────────────────────────────────────────
FROM python:3.12-slim

# Create a non-root user account properly
RUN useradd --no-create-home --uid 1001 vaultflow

WORKDIR /app

# Copy the entire, self-contained virtual environment from the builder
COPY --from=builder /opt/venv /opt/venv

# Copy your core application script
COPY . .

# Enforce secure ownership patterns over the application zone
RUN chown -R vaultflow:vaultflow /app

# Switch executing privileges to the non-root account
USER 1001

# Force the operating system to prioritize our virtual environment binaries and libraries
ENV PATH="/opt/venv/bin:$PATH"
ENV PORT=5000

EXPOSE 5000

CMD ["python", "app.py"]