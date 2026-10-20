"""Own one private local emergency-scene service; never attach or restart."""
from __future__ import annotations
import argparse
import ctypes
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
import urllib.request

if __name__ == "__main__":
    application = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(application), str(application/"tools")]

from portable_source_runtime import load_package, regular, ready_path, json_file, digest
from osgb_stdio_worker import OwnedWindowsJob


def local_request(url, *, owner=None):
    request = urllib.request.Request(url, data=b"" if owner else None,
        headers={"X-Local-Owner": owner} if owner else {},
        method="POST" if owner else "GET")
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request, timeout=5) as response:
        return response.status, response.read(2*1048576+1)


def private_environment(root):
    temp = root/"UserData/Temp"
    for folder in (root/"UserData", temp):
        if not folder.exists():
            folder.mkdir()
        regular(folder, root, directory=True)
    environment = {k: os.environ[k] for k in ("SystemRoot", "WINDIR", "SystemDrive") if k in os.environ}
    environment.update(PATH=str(root/"runtime/python")+os.pathsep+
        str(Path(os.environ.get("SystemRoot", "C:/Windows"))/"System32"),
        TEMP=str(temp), TMP=str(temp), PYTHONIOENCODING="utf-8")
    return environment


def start(root, port=8767, open_browser=True):
    if os.name != "nt":
        raise RuntimeError("The private scene launcher is currently validated on Windows only")
    if type(port) is not int or not 0 <= port <= 65535 or port and port < 1024:
        raise ValueError("Invalid local scene port")
    package = load_package(root)
    root = package["root"]
    if Path(sys.executable).resolve() != (root/"runtime/python/python.exe").resolve():
        raise ValueError("Use this package's private Python runtime")
    if Path(__file__).resolve() != (root/"application/tools/portable_web_entry.py").resolve():
        raise ValueError("Use this package's verified scene entry")
    # Refuse any existing listener; never stop, replace, or attach to it.
    if port:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as check:
            check.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            check.bind(("127.0.0.1", port))
    owner = secrets.token_hex(16)
    ready = ready_path(root, owner)
    journal = ready.with_name(owner+".web_launcher.json")
    environment = private_environment(root)
    report = {"schema":"zhumadian.local.web.owner.v1", "ownerPid":os.getpid(),
        "launchId":owner, "identity":package["identity"], "state":"starting",
        "requestedPort":port, "restartEnabled":False, "ownsService":False}
    sequence = 0
    def record():
        nonlocal sequence
        sequence += 1
        pending = journal.with_name(journal.name+"."+str(sequence)+".pending")
        with pending.open("x", encoding="utf8") as stream:
            json.dump(report, stream, indent=2)
            stream.flush(); os.fsync(stream.fileno())
        pending.replace(journal)
    child = job = None
    record()
    try:
        child = subprocess.Popen([str(root/"runtime/python/python.exe"), "-I", "-B",
            str(root/"application/tools/portable_source_runtime.py"), "--package", str(root),
            "--port", str(port), "--owner-token", owner],
            executable=str(root/"runtime/python/python.exe"), cwd=root,
            env=environment, stdin=subprocess.DEVNULL, close_fds=True,
            creationflags=subprocess.CREATE_NO_WINDOW)
        report["servicePid"] = child.pid
        # The service performs only package preflight before accepting work.
        # On any assignment failure terminate this exact newly created child.
        job = OwnedWindowsJob(child)
        report.update(ownsService=True, jobLimitFlags=job.limit_flags)
        record()
        deadline = time.monotonic()+45
        while not ready.exists():
            if child.poll() is not None:
                raise RuntimeError("Private source service exited before ready: "+str(child.returncode))
            if time.monotonic() >= deadline:
                raise TimeoutError("Private source service did not become ready within 45 seconds")
            time.sleep(.05)
        value, raw = json_file(regular(ready, root), 2*1048576)
        actual_port = value.get("port")
        if (value.get("schema") != "zhumadian.source.runtime.ready.v1"
                or value.get("identity") != package["identity"] or value.get("pid") != child.pid
                or value.get("launchId") != owner or value.get("state") != "ready"
                or value.get("readOnly") is not True or value.get("conversionEnabled") is not False
                or type(actual_port) is not int or not 1024 <= actual_port <= 65535
                or port and actual_port != port):
            raise ValueError("Owned local scene readiness identity differs")
        base = "http://127.0.0.1:"+str(actual_port)
        status, raw = local_request(base+"/api/runtime/status")
        status_value = json.loads(raw)
        if (status != 200 or status_value.get("identity") != package["identity"]
                or status_value.get("pid") != child.pid or status_value.get("readOnly") is not True):
            raise ValueError("Owned local scene HTTP identity differs")
        url = base+"/?topic=emergency&mode=command"
        report.update(state="ready", port=actual_port, url=url)
        record()
        ctypes.windll.kernel32.SetConsoleTitleW("驻马店本地应急三维 - 关闭此窗口停止服务")
        print(json.dumps({"sceneReady":True,"url":url,"ownerPid":os.getpid(),"servicePid":child.pid}), flush=True)
        if open_browser:
            try:
                os.startfile(url)
                report["browserRequested"] = True
            except OSError as error:
                report["browserError"] = str(error)
            record()
        try:
            code = child.wait()
            report["serviceExitCode"] = code
            if code:
                raise RuntimeError("Owned local scene service exited: "+str(code))
        except KeyboardInterrupt:
            report["stopReason"] = "console_interrupt"
    except BaseException as error:
        report.update(state="failed", error=str(error))
        raise
    finally:
        if child is not None and child.poll() is None:
            if report.get("state") == "ready":
                try:
                    status, _ = local_request("http://127.0.0.1:"+str(report["port"])+"/api/runtime/shutdown", owner=owner)
                    report["shutdownHttpStatus"] = status
                    child.wait(timeout=10)
                except Exception as error:
                    report["shutdownError"] = str(error)
            if child.poll() is None:
                # Job closure collects only our own service and its reader.
                if job is not None:
                    job.close()
                if child.poll() is None:
                    child.kill()
                child.wait(timeout=10)
                report["forcedOwnedStop"] = True
        if job is not None:
            job.close()
        if child is not None:
            report["serviceExitCode"] = child.returncode
        if report.get("state") != "failed":
            report["state"] = "stopped"
        record()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8767)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    start(args.package, args.port, not args.no_browser)


if __name__ == "__main__":
    main()
