#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
echo "Working directory: $(pwd)"

echo "Running: python3 EdSum.py --last 1d --to \"Ed Summary\""
python3 EdSum.py --last 1d --to "Ed Summary"
echo "Done"
