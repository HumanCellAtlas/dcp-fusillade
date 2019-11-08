#!/usr/bin/env python3
#
# Entry point for local testing of zappa app

from app import create_app

app = create_app({"LOCAL": True})

if __name__ == "__main__":
    app.run()

