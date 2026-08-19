#!/usr/bin/env bash
# Run the full seo-aeo test suite. No network, no dependencies.
set -euo pipefail
cd "$(dirname "$0")"
echo "== unit + integration =="
python3 test_seo_aeo.py "$@"
echo
echo "== site archetypes (generality) =="
python3 test_site_archetypes.py "$@"
