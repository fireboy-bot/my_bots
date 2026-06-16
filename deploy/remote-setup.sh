#!/bin/bash
set -euo pipefail

REMOTE_DIR="/opt/chislyandia"

mkdir -p "$REMOTE_DIR"
tar -xzf /tmp/chislyandia-deploy.tgz -C "$REMOTE_DIR"
chown -R juliabot:juliabot "$REMOTE_DIR"
mkdir -p "$REMOTE_DIR/data" "$REMOTE_DIR/logs"
chmod -R u+rwX "$REMOTE_DIR/data" "$REMOTE_DIR/logs"
chown -R juliabot:juliabot "$REMOTE_DIR/data" "$REMOTE_DIR/logs"

if [ ! -d "$REMOTE_DIR/venv" ]; then
  python3 -m venv "$REMOTE_DIR/venv"
fi
"$REMOTE_DIR/venv/bin/pip" install -q -U pip
"$REMOTE_DIR/venv/bin/pip" install -q -r "$REMOTE_DIR/requirements-web.txt"

cd "$REMOTE_DIR"
"$REMOTE_DIR/venv/bin/python" -c "from database.schema import init_database; init_database('data/progress.db')"

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq nginx

cp "$REMOTE_DIR/deploy/chislyandia-api.service" /etc/systemd/system/chislyandia-api.service
cp "$REMOTE_DIR/deploy/nginx-chislyandia.conf" /etc/nginx/sites-available/chislyandia
ln -sf /etc/nginx/sites-available/chislyandia /etc/nginx/sites-enabled/chislyandia
rm -f /etc/nginx/sites-enabled/default

systemctl daemon-reload
systemctl enable chislyandia-api nginx
systemctl restart chislyandia-api nginx

sleep 3
curl -sf http://127.0.0.1:5000/api/health
curl -sf http://127.0.0.1/api/health
echo "DEPLOY_OK"
