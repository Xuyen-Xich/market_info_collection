#!/usr/bin/env python3
"""Test main.py with verbose logging."""

import sys
from pathlib import Path
from loguru import logger

# Setup logging
logger.remove()  # Remove default handler
logger.add(sys.stderr, level="DEBUG", format="<level>{level: <8}</level> | {message}")

# Now run main
from main import main

if __name__ == "__main__":
    # Set args
    sys.argv = [
        "main.py",
        "--urls-file", "urls.txt",
        "--headless",
        "--max-delay", "3",
    ]
    main()
