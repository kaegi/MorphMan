#!/usr/bin/env bash

echo "
----------------------
  Setting up dev environment
----------------------
"
chmod +x .githooks/pre-commit
git config core.hooksPath .githooks
find .git/hooks -type l -exec rm {} \; && find .githooks -type f -exec ln -sf ../../{} .git/hooks/ \;
