"""Start the demo the easy way:

    python -m app

Honours a few environment variables (all optional):

    HOST     interface to bind (default 127.0.0.1)
    PORT     port to listen on  (default 8000)
    RELOAD   set to 1/true to auto-reload on code changes
"""

from __future__ import annotations

import os


def main() -> None:
    import uvicorn

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    reload = os.environ.get("RELOAD", "").lower() in {"1", "true", "yes", "on"}

    banner = (
        "\n  AI Customer Support Platform"
        f"\n  Web UI    ->  http://localhost:{port}/"
        f"\n  API docs  ->  http://localhost:{port}/docs"
        "\n  Press CTRL+C to stop.\n"
    )
    print(banner, flush=True)

    uvicorn.run("api.main:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()
