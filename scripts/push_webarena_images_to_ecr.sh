#!/usr/bin/env bash
# push_webarena_images_to_ecr.sh
#
# One-time script to push the pre-built WebArena shopping images to ECR.
# Run this locally before the first deployment, and again only if the
# upstream images are updated.
#
# Prerequisites:
#   - AWS CLI configured with credentials for account 236208139397
#   - Docker running locally
#   - Sufficient local disk space (~20GB free)
#
# Usage:
#   bash scripts/push_webarena_images_to_ecr.sh

set -euo pipefail

ACCOUNT_ID="236208139397"
REGION="us-east-1"
APP_NAME="webarena"
REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

SHOPPING_URL="http://metis.lti.cs.cmu.edu/webarena-images/shopping_final_0712.tar"
SHOPPING_ADMIN_URL="http://metis.lti.cs.cmu.edu/webarena-images/shopping_admin_final_0719.tar"

echo "==> Logging in to ECR..."
aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "$REGISTRY"

push_image() {
  local url="$1"
  local service="$2"
  local ecr_repo="${REGISTRY}/${APP_NAME}/${service}"

  echo ""
  echo "==> [${service}] Creating ECR repository if needed..."
  aws ecr describe-repositories --repository-names "${APP_NAME}/${service}" --region "$REGION" \
    || aws ecr create-repository --repository-name "${APP_NAME}/${service}" --region "$REGION"

  echo "==> [${service}] Streaming image from source into Docker..."
  LOAD_OUTPUT=$(curl -fL "$url" | docker load)
  echo "$LOAD_OUTPUT"
  SOURCE=$(echo "$LOAD_OUTPUT" | tail -1 | awk '{print $NF}')

  echo "==> [${service}] Tagging and pushing to ${ecr_repo}:latest..."
  docker tag "$SOURCE" "${ecr_repo}:latest"
  docker push "${ecr_repo}:latest"

  echo "==> [${service}] Cleaning up local image..."
  docker rmi "$SOURCE" "${ecr_repo}:latest" || true

  echo "==> [${service}] Done."
}

push_image "$SHOPPING_URL"       "shopping"
push_image "$SHOPPING_ADMIN_URL" "shopping-admin"

echo ""
echo "All images pushed to ECR. You can now run the Dev Deploy workflow."
