"""python -m nebula : start the command server and open the strategy interface."""

import argparse
import threading
import webbrowser

import uvicorn


def main():
    parser = argparse.ArgumentParser(description="NEBULA")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    url = f"http://127.0.0.1:{args.port}"
    print(f"NEBULA command is at {url}  (Ctrl+C to stop)")
    if not args.no_browser:
        threading.Timer(1.2, webbrowser.open, [url]).start()
    uvicorn.run("nebula.api:app", host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
