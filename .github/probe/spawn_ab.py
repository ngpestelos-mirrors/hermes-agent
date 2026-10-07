"""Spawn Git bash many times from W parallel workers per env variant; count non-zero exits."""
import os, subprocess, sys, tempfile, collections
from concurrent.futures import ThreadPoolExecutor
from hermes_platform.resolver import locate_command

bash = locate_command("bash").command[0]
git = locate_command("git").command[0]
interp = os.path.dirname(sys.executable)
SCRIPT = 'record() { :; }\nx=$(printf a | tr a b)\n[ "$x" = b ]\nif false; then echo no; fi\n'
d = tempfile.mkdtemp(prefix="ab-")
script = os.path.join(d, "s.sh"); open(script, "w").write(SCRIPT)
base = {"PATH": os.pathsep.join((interp, os.defpath, os.path.dirname(bash), os.path.dirname(git))),
        "HOME": d, "RUNNER_TEMP": d}
win = {k: os.environ[k] for k in os.environ if k.upper() in (
    "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "SYSTEMDRIVE", "TEMP", "TMP", "PROGRAMDATA",
    "PROCESSOR_ARCHITECTURE", "NUMBER_OF_PROCESSORS", "USERPROFILE", "LOCALAPPDATA", "APPDATA")}
print("bash:", bash, "win keys:", sorted(win))
variants = {"minimal": base, "minimal+windows": {**base, **win}}
mode = sys.argv[1]; n = int(sys.argv[2]); workers = int(sys.argv[3])
env = variants[mode]
def one(_):
    r = subprocess.run([bash, "--noprofile", "--norc", "-eo", "pipefail", script], cwd=d, env=env,
                       stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)
    return r.returncode
with ThreadPoolExecutor(workers) as ex:
    codes = collections.Counter(ex.map(one, range(n)))
bad = sum(v for k, v in codes.items() if k != 0)
print(f"AB {mode}: bad={bad}/{n} codes={dict((hex(k & 0xFFFFFFFF), v) for k, v in codes.items())}")
