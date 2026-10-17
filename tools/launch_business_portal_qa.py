"""Launch only the explicit synthetic QA portal, preserving existing owned sessions."""

import argparse, json, subprocess, sys, time, urllib.request, webbrowser
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8790)
    p.add_argument("--no-browser", action="store_true")
    p.add_argument("--page",choices=("scene","portal"),default="scene")
    a = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    url = f"http://127.0.0.1:{a.port}"

    def healthy():
        try:
            with urllib.request.urlopen(url + "/qa/status", timeout=1) as response:
                d = json.load(response)
                return (
                    d.get("synthetic") is True
                    and d.get("stage") == "XNBY business portal QA 0.7"
                )
        except Exception:
            return False

    if not healthy():
        logs = root.parent / "Document/Deployment/web_auth_20261014"
        logs.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        with (logs / f"qa_{stamp}.out.log").open("wb") as stream:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(root / "tools/serve_business_portal_qa.py"),
                    "--port",
                    str(a.port),
                ],
                cwd=root,
                stdout=stream,
                stderr=subprocess.STDOUT,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                ),
            )
        (logs / f"qa_{stamp}.pid").write_text(str(process.pid))
        for _ in range(40):
            if healthy():
                break
            if process.poll() is not None:
                raise RuntimeError("QA portal failed to start; inspect its log.")
            time.sleep(0.15)
        else:
            raise RuntimeError("QA portal is not ready; inspect its log.")
    if a.page=="portal":url+="/portal.html#hidden-danger"
    print("XNBY SYNTHETIC QA ONLY:", url)
    if not a.no_browser:
        webbrowser.open(url)


if __name__ == "__main__":
    main()
