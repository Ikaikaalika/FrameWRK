#!/usr/bin/env bash
# Usage: sudo bash run_on_aws.sh <ZIP_URL> "<ENV_CONTENTS>"
set -euxo pipefail
ZIP_URL="${1:-}"
ENV_CONTENTS="${2:-}"

if [[ -z "$ZIP_URL" ]]; then
  echo "Provide a public ZIP_URL to the project archive"
  exit 1
fi

apt-get update
apt-get install -y docker.io unzip curl git
systemctl enable --now docker

cd /opt
curl -L -o ai-app.zip "$ZIP_URL"
unzip -o ai-app.zip
cd ai-starter

echo "$ENV_CONTENTS" > .env

cat > deploy/aws/scripts/nginx.conf <<'NGINX'
events {}
http {
  server {
    listen 80;
    location / {
      proxy_pass http://frontend:3000;
    }
  }
}
NGINX

docker rm -f nginx || true
docker compose up -d --build
docker run -d --name nginx --network ai-starter_default -p 80:80 --restart unless-stopped   -v $(pwd)/deploy/aws/scripts/nginx.conf:/etc/nginx/nginx.conf:ro nginx:alpine || true

echo "UI:  http://$(curl -s ifconfig.me)"
echo "API: http://$(curl -s ifconfig.me):8000/docs"
