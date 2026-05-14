# ── Build stage ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Final stage ──────────────────────────────────────────────────────────
FROM python:3.12-slim

# Create non-root user — required for PSA restricted
RUN useradd --no-create-home --uid 1001 vaultflow

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/vaultflow/.local

# Copy application code
COPY app.py .

# Set ownership
RUN chown -R vaultflow:vaultflow /app

# Switch to non-root user
USER 1001

ENV PATH=/home/vaultflow/.local/bin:$PATH
ENV PORT=5000

EXPOSE 5000

CMD ["python", "app.py"]