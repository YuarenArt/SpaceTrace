#!/usr/bin/env bash
# Run real QGIS interface scenarios on an isolated virtual display.
set -euo pipefail
export DISPLAY=:99
export QT_QPA_PLATFORM=xcb
Xvfb "$DISPLAY" -screen 0 1280x1024x24 -ac -noreset -nolisten tcp &
xvfb_pid=$!
trap 'kill "$xvfb_pid" 2>/dev/null || true' EXIT
for _ in {1..40}; do
    if [ -S /tmp/.X11-unix/X99 ]; then
        "$@"
        exit $?
    fi
    if ! kill -0 "$xvfb_pid" 2>/dev/null; then
        echo 'Xvfb failed to start' >&2
        exit 1
    fi
    sleep 0.25
done
echo 'Timed out waiting for Xvfb' >&2
exit 1
