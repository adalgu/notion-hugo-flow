# Multi-stage Docker build for production optimization
# Stage 1: Build Environment
FROM ubuntu:22.04 as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    wget \
    python3 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Hugo (standardized version)
ARG HUGO_VERSION=0.140.0
RUN wget -O /tmp/hugo.deb https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.deb \
    && dpkg -i /tmp/hugo.deb \
    && rm /tmp/hugo.deb

WORKDIR /app

# Copy production dependencies first (better caching)
COPY requirements.prod.txt ./
RUN pip3 install --no-cache-dir -r requirements.prod.txt

# Copy only necessary source files
COPY src/ src/
COPY notion_hugo_app.py .
COPY config/ config/
COPY themes/ themes/
COPY layouts/ layouts/
COPY static/ static/
COPY archetypes/ archetypes/
COPY notion-hugo.config.yaml .

# Stage 2: Production Runtime (for static hosting)
FROM nginx:alpine as production

# Copy only the built static files (if public exists)
COPY public/ /usr/share/nginx/html/ 2>/dev/null || echo "No public directory to copy"

# Stage 3: Development Runtime (for local development)
FROM builder as development

# Add development dependencies
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy development files
COPY . .

# Create directory for temporary files
RUN mkdir -p /app/data/error_temp

EXPOSE 1313
CMD ["hugo", "server", "--bind=0.0.0.0", "--port=1313", "--buildDrafts"]

# Stage 4: Application Runner (for sync operations) - DEFAULT
FROM builder as app

# Copy application configuration
COPY notion-hugo.config.yaml* ./

# Create directory for temporary files
RUN mkdir -p /app/data/error_temp

# Set environment variables
ENV PYTHONPATH=/app
ENV HUGO_ENVIRONMENT=production

# Default command for sync operations
ENTRYPOINT ["python3", "notion_hugo_app.py"]
CMD ["--hugo-args=server --bind=0.0.0.0"]
