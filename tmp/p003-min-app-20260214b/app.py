from __future__ import annotations

import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


def main() -> None:
    port = int(os.environ.get("PORT", "8498"))
    directory = os.environ.get("APP_DIR") or os.path.dirname(__file__)
    os.chdir(directory)
    server = ThreadingHTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
