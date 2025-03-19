#!/bin/bash

# Set working directory to project root
cd "$(dirname "$0")/../.."
ROOT_DIR=$(pwd)
echo "Working directory: $ROOT_DIR"

# Deploy to Render with production flag
echo "🚀 Deploying to Render production..."
render deploy

# Wait for deployment to complete
echo "⏱️ Waiting for deployment to complete..."
echo "This can take a few minutes. Please wait..."
echo "NOTE: The database will be initialized automatically via the preDeployCommand"
echo "      configured in render.yaml. No manual initialization needed."
echo
echo "✅ Deployment initiated! Check the Render dashboard for progress."