#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'volunteer.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Install dependencies and run with the virtual environment Python.\n"
            "PowerShell example:\n"
            "  .\\venv\\Scripts\\python.exe manage.py runserver\n"
            "If you already activated venv, run:\n"
            "  python manage.py runserver"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
