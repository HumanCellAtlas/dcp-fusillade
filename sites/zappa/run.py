#!/usr/bin/env python3
#
# Main entry point for the zappa app

from .app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
