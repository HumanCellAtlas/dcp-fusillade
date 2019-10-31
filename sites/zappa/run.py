#!/usr/bin/env python3
#
# Main entry point for the zappa app

import os
from app import create_app

app = create_app(os.environ.get('FUS_STAGE_TAG'))

if __name__ == "__main__":
    app.run()
