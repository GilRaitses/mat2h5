#!/usr/bin/env python3
"""
CLI shim for the installed `magatfairy` command.

Delegates directly to the packaged main in magatfairy_app.
"""

import sys
from magatfairy_app.main import main


if __name__ == "__main__":
    sys.exit(main())


