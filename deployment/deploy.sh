#!/bin/bash
# Carbon Room - Quick Deploy Script
# Usage: ./deploy.sh [siteground|render|local]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DEPLOY_TARGET="${1:-local}"

echo "========================================"
echo "CARBON ROOM DEPLOYMENT"
echo "========================================"
echo "Target: $DEPLOY_TARGET"
echo "Project: $PROJECT_DIR"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Pre-flight checks
preflight_check() {
    log_info "Running pre-flight checks..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 not found"
        exit 1
    fi
    log_info "Python: $(python3 --version)"

    # Check required files
    if [ ! -f "$PROJECT_DIR/api/server.py" ]; then
        log_error "api/server.py not found"
        exit 1
    fi

    if [ ! -f "$PROJECT_DIR/deployment/requirements.txt" ]; then
        log_error "deployment/requirements.txt not found"
        exit 1
    fi

    log_info "Pre-flight checks passed"
}

# Build deployment package
build_package() {
    log_info "Building deployment package..."

    BUILD_DIR="$PROJECT_DIR/dist"
    rm -rf "$BUILD_DIR"
    mkdir -p "$BUILD_DIR"

    # Copy application files
    cp -r "$PROJECT_DIR/api" "$BUILD_DIR/"
    [ -d "$PROJECT_DIR/templates" ] && cp -r "$PROJECT_DIR/templates" "$BUILD_DIR/"
    [ -d "$PROJECT_DIR/static" ] && cp -r "$PROJECT_DIR/static" "$BUILD_DIR/"

    # Copy deployment configs
    cp "$SCRIPT_DIR/passenger_wsgi.py" "$BUILD_DIR/"
    cp "$SCRIPT_DIR/requirements.txt" "$BUILD_DIR/"
    cp "$SCRIPT_DIR/.htaccess" "$BUILD_DIR/"
    cp "$SCRIPT_DIR/.env.production" "$BUILD_DIR/.env.template"

    # Create required directories
    mkdir -p "$BUILD_DIR/vault"
    mkdir -p "$BUILD_DIR/telemetry"
    mkdir -p "$BUILD_DIR/tmp"

    # Create archive
    cd "$BUILD_DIR"
    tar -czf "$PROJECT_DIR/carbon-room-deploy.tar.gz" .

    log_info "Package built: $PROJECT_DIR/carbon-room-deploy.tar.gz"
}

# Deploy to local (for testing)
deploy_local() {
    log_info "Deploying locally for testing..."

    cd "$PROJECT_DIR"

    # Create virtual environment if not exists
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
    fi

    # Activate and install
    source .venv/bin/activate
    pip install -r deployment/requirements.txt

    # Run server
    log_info "Starting server on http://localhost:8003"
    python -m uvicorn api.server:app --host 0.0.0.0 --port 8003 --reload
}

# Deploy to SiteGround
deploy_siteground() {
    log_info "Deploying to SiteGround..."

    # Check for SSH config
    if [ -z "$SITEGROUND_HOST" ] || [ -z "$SITEGROUND_USER" ]; then
        log_error "Set SITEGROUND_HOST and SITEGROUND_USER environment variables"
        log_info "Example: export SITEGROUND_HOST=your-server-ip"
        log_info "Example: export SITEGROUND_USER=your-cpanel-user"
        exit 1
    fi

    SSH_PORT="${SITEGROUND_PORT:-18765}"
    REMOTE_DIR="~/thecarbon6.agency"

    # Build package first
    build_package

    # Upload via SCP
    log_info "Uploading to $SITEGROUND_USER@$SITEGROUND_HOST..."
    scp -P "$SSH_PORT" "$PROJECT_DIR/carbon-room-deploy.tar.gz" \
        "$SITEGROUND_USER@$SITEGROUND_HOST:$REMOTE_DIR/"

    # Extract and setup on server
    log_info "Setting up on server..."
    ssh -p "$SSH_PORT" "$SITEGROUND_USER@$SITEGROUND_HOST" << 'REMOTE_SCRIPT'
        cd ~/thecarbon6.agency
        tar -xzf carbon-room-deploy.tar.gz
        rm carbon-room-deploy.tar.gz

        # Activate virtualenv and install deps
        source ~/virtualenv/thecarbon6.agency/3.9/bin/activate
        pip install -r requirements.txt --quiet

        # Set permissions
        chmod 755 .
        chmod 750 vault telemetry
        chmod 644 passenger_wsgi.py

        # Restart Passenger
        mkdir -p tmp
        touch tmp/restart.txt

        echo "Deployment complete!"
REMOTE_SCRIPT

    log_info "SiteGround deployment complete"
    log_info "Visit: https://thecarbon6.agency"
}

# Deploy to Render
deploy_render() {
    log_info "Deploying to Render..."

    if [ -z "$RENDER_API_KEY" ] || [ -z "$RENDER_SERVICE_ID" ]; then
        log_error "Set RENDER_API_KEY and RENDER_SERVICE_ID environment variables"
        exit 1
    fi

    curl -X POST \
        -H "Authorization: Bearer $RENDER_API_KEY" \
        -H "Content-Type: application/json" \
        "https://api.render.com/v1/services/$RENDER_SERVICE_ID/deploys"

    log_info "Render deployment triggered"
    log_info "Check dashboard: https://dashboard.render.com"
}

# Main
case "$DEPLOY_TARGET" in
    local)
        preflight_check
        deploy_local
        ;;
    siteground)
        preflight_check
        deploy_siteground
        ;;
    render)
        preflight_check
        deploy_render
        ;;
    build)
        preflight_check
        build_package
        ;;
    *)
        echo "Usage: $0 [local|siteground|render|build]"
        echo ""
        echo "Options:"
        echo "  local      - Run locally for testing (default)"
        echo "  siteground - Deploy to SiteGround"
        echo "  render     - Trigger Render deployment"
        echo "  build      - Build deployment package only"
        exit 1
        ;;
esac
