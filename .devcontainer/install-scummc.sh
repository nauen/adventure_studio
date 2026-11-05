#!/usr/bin/env bash
set -euo pipefail

# Pinned, research-only ScummC compiler; no source files are vendored.
SCUMMC_REVISION="2f61ce0f7b5051e920876dc4b71935dc99f38fff"
SCUMMC_DIRECTORY="${HOME}/.cache/adventure-studio/scummc"

if test -f "$SCUMMC_DIRECTORY/.adventure-studio-revision" && test "$(cat "$SCUMMC_DIRECTORY/.adventure-studio-revision")" = "$SCUMMC_REVISION"; then
  echo "ScummC already installed at $SCUMMC_DIRECTORY"
  exit 0
fi

sudo apt-get -o Acquire::Retries=4 -o Acquire::http::Timeout=45 update
sudo env DEBIAN_FRONTEND=noninteractive apt-get -y --no-install-recommends -o Acquire::Retries=4 -o Acquire::http::Timeout=45 install build-essential bison flex xsltproc pkg-config libglib2.0-dev
mkdir -p "$SCUMMC_DIRECTORY"
git -C "$SCUMMC_DIRECTORY" init
git -C "$SCUMMC_DIRECTORY" fetch --depth 1 https://github.com/AlbanBedel/scummc.git "$SCUMMC_REVISION"
git -C "$SCUMMC_DIRECTORY" checkout --detach FETCH_HEAD

test -f "$SCUMMC_DIRECTORY/man/tools/scc.xml"
test -f "$SCUMMC_DIRECTORY/man/tools/header.xslt"
grep -Fq '$(SRCDIR)/man/%.xml' "$SCUMMC_DIRECTORY/Makefile.target"
sed -i 's@$(SRCDIR)/man/%.xml@$(SRCDIR)/man/tools/%.xml@g; s@$(SRCDIR)/man/header.xslt@$(SRCDIR)/man/tools/header.xslt@g' "$SCUMMC_DIRECTORY/Makefile.target"
(
  cd "$SCUMMC_DIRECTORY"
  ./configure
  make -j2
)
test -n "$(find "$SCUMMC_DIRECTORY" -type f -name scc -executable -print -quit)"
test -n "$(find "$SCUMMC_DIRECTORY" -type f -name sld -executable -print -quit)"
printf '%s\n' "$SCUMMC_REVISION" > "$SCUMMC_DIRECTORY/.adventure-studio-revision"
echo "Pinned ScummC $SCUMMC_REVISION built at $SCUMMC_DIRECTORY"
