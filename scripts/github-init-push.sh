#!/usr/bin/env bash
set -euo pipefail
REPO_NAME="SiteHub_Center"
PROXY_GATEWAY="${PROXY_GATEWAY:-}"
if [[ -n "$PROXY_GATEWAY" ]]; then
  export http_proxy="$PROXY_GATEWAY"
  export https_proxy="$PROXY_GATEWAY"
fi
if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "ERR: Please export GITHUB_TOKEN with repo scope."
  exit 2
fi
HTTP_STATUS="$(curl -s -o /tmp/create_repo_resp.json -w "%{http_code}" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  -H "Accept: application/vnd.github+json" \
  -d "{\"name\":\"${REPO_NAME}\",\"private\":true,\"auto_init\":false,\"description\":\"SiteHub_Center\"}" \
  https://api.github.com/user/repos || true)"
if [[ "$HTTP_STATUS" != "201" && "$HTTP_STATUS" != "422" ]]; then
  echo "ERR: Failed to create repo (status ${HTTP_STATUS})."
  exit 4
fi
OWNER=""
if [[ "$HTTP_STATUS" == "201" ]]; then
  OWNER="$(sed -n 's|.*\"full_name\": *\"\\([^/]*\\)/[^\"]*\".*|\\1|p' /tmp/create_repo_resp.json)"
fi
if [[ -z "$OWNER" ]]; then
  OWNER="${GITHUB_OWNER:-}"
fi
if [[ -z "$OWNER" ]]; then
  OWNER="$(curl -s -H "Authorization: Bearer ${GITHUB_TOKEN}" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" https://api.github.com/user | sed -n 's/.*\"login\": *\"\\([^\"]*\\)\".*/\\1/p')"
fi
if [[ -z "$OWNER" ]]; then
  echo "ERR: Unable to resolve GitHub owner. Set GITHUB_OWNER env."
  exit 3
fi
git remote | grep -q "^origin$" || git remote add origin "https://github.com/${OWNER}/${REPO_NAME}.git"
AUTH_B64="$(printf "oauth2:${GITHUB_TOKEN}" | base64 -w 0)"
git -c http.extraHeader="Authorization: Basic ${AUTH_B64}" push "https://github.com/${OWNER}/${REPO_NAME}.git" main
git remote set-url origin "https://github.com/${OWNER}/${REPO_NAME}.git"
echo "OK: Pushed to https://github.com/${OWNER}/${REPO_NAME}.git (main)"
