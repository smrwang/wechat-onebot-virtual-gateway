#!/bin/sh
set -eu

export DISPLAY="${DISPLAY:-:99}"
export XDG_RUNTIME_DIR=/tmp/runtime-wechat
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"
mkdir -p /root/.xwechat/adapter
test -f /root/.xwechat/adapter/contacts.json || printf '{}\n' > /root/.xwechat/adapter/contacts.json

Xvfb "$DISPLAY" -screen 0 1280x800x24 -nolisten tcp &
XVFB_PID=$!

cleanup() {
  kill "$XVFB_PID" 2>/dev/null || true
  exit 0
}
trap cleanup INT TERM

for _ in $(seq 1 100); do
  if test -S "/tmp/.X11-unix/X${DISPLAY#:}" && xset -display "$DISPLAY" q >/dev/null 2>&1; then
    break
  fi
  sleep 0.1
done
test -S "/tmp/.X11-unix/X${DISPLAY#:}" && xset -display "$DISPLAY" q >/dev/null 2>&1 || { echo "Xvfb did not become ready" >&2; exit 1; }
echo "Xvfb ready on $DISPLAY"

# Milestone 0 keeps the GUI supervisor deliberately simple. Start a
# dedicated D-Bus session for the GUI and AT-SPI registry in this container.
dbus-run-session -- sh -c '
  /usr/libexec/at-spi2-registryd >/proc/1/fd/1 2>/proc/1/fd/2 &
  openbox >/proc/1/fd/1 2>/proc/1/fd/2 &
  wechat >/proc/1/fd/1 2>/proc/1/fd/2 &
  x11vnc -display "$DISPLAY" -forever -shared -rfbport "$VNC_PORT" -nopw -localhost >/proc/1/fd/1 2>/proc/1/fd/2 &
  websockify --web /usr/share/novnc "$NOVNC_PORT" "localhost:$VNC_PORT" >/proc/1/fd/1 2>/proc/1/fd/2 &
  python3 /usr/local/bin/dashboard.py >/proc/1/fd/1 2>/proc/1/fd/2 &
  PYTHONPATH=/usr/local/lib python3 -m ui_worker.service >/proc/1/fd/1 2>/proc/1/fd/2 &
  (while true; do python3 /usr/local/bin/ui_probe.py >/proc/1/fd/1 2>/proc/1/fd/2 || true; python3 /usr/local/bin/x11_probe.py >/proc/1/fd/1 2>/proc/1/fd/2 || true; sleep 2; done) &
  # Keep the container alive independently of any test window. All long-lived
  # services remain children of this D-Bus session.
  while true; do sleep 3600; done
'
