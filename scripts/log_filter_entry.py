#!/usr/bin/env python3
"""
Skill-friendly entrypoint for the embedded log-filter tool.

This wrapper allows running the tool from another project via:
    python scripts/log_filter_entry.py --expression "ERROR" --path ./logs
"""

from __future__ import annotations

import sys
from multiprocessing import freeze_support

from log_filter.main import main


if __name__ == "__main__":
    freeze_support()
    sys.exit(main())
