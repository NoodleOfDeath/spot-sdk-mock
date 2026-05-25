#!/usr/bin/env bash
# Download the Sketchfab "Boston Dynamics — Spot" GLB and place it at
# mocks/web_mock/public/spot.glb.
#
# The model is CC-BY 4.0 (author: Ashish0096), but Sketchfab's download
# endpoint requires an account token. Get one at
#   https://sketchfab.com/settings/password
# and run:
#
#   SKETCHFAB_API_TOKEN=<token> ./scripts/fetch_spot_model.sh
#
# After the file lands, ``git add`` it — Git LFS picks it up via
# ``.gitattributes`` (``*.glb filter=lfs``).
set -euo pipefail

MODEL_UID="71354fd599e34db898a7d083851b792a"
OUT_DIR="mocks/web_mock/public"
OUT_PATH="${OUT_DIR}/spot.glb"

if [[ -z "${SKETCHFAB_API_TOKEN:-}" ]]; then
  echo "error: set SKETCHFAB_API_TOKEN first (https://sketchfab.com/settings/password)" >&2
  exit 1
fi

mkdir -p "${OUT_DIR}"

echo "Fetching download URLs for ${MODEL_UID}…"
DL_JSON=$(curl -sf -H "Authorization: Token ${SKETCHFAB_API_TOKEN}" \
  "https://api.sketchfab.com/v3/models/${MODEL_UID}/download")

GLB_URL=$(printf '%s' "${DL_JSON}" | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(d.get('glb',{}).get('url',''))")

if [[ -z "${GLB_URL}" ]]; then
  echo "error: no glb url in download response" >&2
  printf '%s\n' "${DL_JSON}" >&2
  exit 1
fi

echo "Downloading GLB → ${OUT_PATH}"
curl -fL --progress-bar "${GLB_URL}" -o "${OUT_PATH}"

echo "Done. Size: $(du -h "${OUT_PATH}" | cut -f1)"
echo "Add via Git LFS:  git add ${OUT_PATH} && git commit -m 'add spot model (LFS)'"
