#!/usr/bin/env bash
set -euo pipefail

cd frontend

cat > public/runtime-config.js <<EOF
window.__RUNTIME_CONFIG__ = {
  API_BASE: "${API_BASE:-}",
};
EOF

npm ci
npm run build
