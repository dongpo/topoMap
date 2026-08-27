#!/bin/sh
set -eu
cd "$(dirname "$0")"
shasum -a 256 -c CHECKSUMS.sha256
