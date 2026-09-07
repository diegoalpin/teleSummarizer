#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
echo "Working directory: $(pwd)"

echo "Running: python3 EdSum.py --mode hours --value 12"
python3 EdSum.py --mode hours --value 12
echo "Done"
