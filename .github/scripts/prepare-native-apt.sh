#!/usr/bin/env bash
set -euo pipefail
# Restrict normalization to active APT source files, including legacy .list.
while IFS= read -r -d '' file; do
    sudo sed -Ei 's@https?://([a-zA-Z0-9.-]+\.)?archive\.ubuntu\.com/ubuntu@https://archive.ubuntu.com/ubuntu@g' "$file"
done < <(find /etc/apt -maxdepth 2 -type f \( -name '*.list' -o -name '*.sources' \) -print0)
# Verify the actual APT index targets rather than assuming a particular file.
sudo apt-get -o Acquire::Retries=3 -o Acquire::https::Timeout=45 -o Acquire::http::Timeout=45 update
targets="$(apt-get indextargets --format '$(URI)')"
printf '%s\n' "$targets"
if grep -Eq 'https?://[^/]+\.archive\.ubuntu\.com/' <<< "$targets"; then
    echo 'Unexpected regional Ubuntu archive remains active' >&2
    exit 1
fi
