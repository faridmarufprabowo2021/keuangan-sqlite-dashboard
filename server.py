#!/usr/bin/env python3
"""Main entry point for Valuta Financial Dashboard Server."""

import os
import sys
from http.server import ThreadingHTTPServer

from app.api import FinanceAPIHandler
from app.database import init_db
from seed import seed

PORT = 8090
HOST = "0.0.0.0"

def main():
    print("=" * 60)
    print("  VALUTA — Precision Financial Dashboard OS (SQLite)")
    print("  Anti-Slop Design Taste Standard (Linear / Mercury / Figma)")
    print("=" * 60)

    # Initialize database & ensure initial seed exists
    init_db()
    seed()

    server_address = (HOST, PORT)
    httpd = ThreadingHTTPServer(server_address, FinanceAPIHandler)
    print(f"\n[OK] Server running at http://localhost:{PORT}")
    print(f"[OK] Ready for desktop & mobile access\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server gracefully...")
        httpd.server_close()
        sys.exit(0)

if __name__ == "__main__":
    main()
