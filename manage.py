#!/usr/bin/env python
"""Django management entry point."""
import os
import sys

from django.core.management import execute_from_command_line
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
