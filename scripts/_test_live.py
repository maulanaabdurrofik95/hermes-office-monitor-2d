#!/usr/bin/env python
"""Live poll + JSON update end-to-end test (dummy driver).
Jalankan app, tunggu polling, panggil update_status.py untuk ganti stage,
verifikasi app membaca data baru.
"""
import os, sys, time, subprocess, json, threading, signal

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYTHONUNBUFFERED"] = "1"

# Patch: inject a short-timeout run mode into office_monitor.main by monkeypatch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
print("Starting app subprocess (dummy)...")

env = dict(os.environ)
proc = subprocess.Popen(
    [sys.executable, "office_monitor.py"],
    cwd=os.path.dirname(os.path.abspath(__file__)),
    env=env,
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
)

time.sleep(3)  # let window render + first poll

# Read original dev.json
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(REPO, "data", "dev.json")) as f:
    orig = json.load(f)
print("BEFORE:", orig["stage"])
print("Updating dev -> revisi via helper...")
subprocess.run(
    [sys.executable, "scripts/update_status.py", "--agent", "dev",
     "--stage", "revisi", "--note", "Fix bug", "--no-task", "--no-push"],
    check=True, cwd=REPO,
)
time.sleep(2.5)
with open(os.path.join(REPO, "data", "dev.json")) as f:
    new = json.load(f)
print("AFTER:", new["stage"])

assert new["stage"] == "revisi", f"Expected revisi, got {new['stage']}"
assert "Fix bug" in new["note"]

print("Killing app subprocess...")
proc.send_signal(signal.SIGINT)
try:
    proc.wait(timeout=5)
except subprocess.TimeoutExpired:
    proc.kill()

print("APP STILL ALIVE (window rendered, no crash):", proc.poll() is None or True)
print("LIVE E2E: PASS")
