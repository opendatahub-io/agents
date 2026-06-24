"""CLI entry point for the Log Monitor Agent.

Usage:
    python -m log_monitor_agent "ERROR: Database connection failed"
    python -m log_monitor_agent "WARNING: Memory usage at 85%"
    python -m log_monitor_agent "INFO: Application started"
"""

import sys

from .agent import process_log_message


def main() -> None:
    """Main entry point for CLI usage."""
    if len(sys.argv) < 2:
        print("Usage: python -m log_monitor_agent <log_message>")
        print()
        print("Examples:")
        print('  python -m log_monitor_agent "ERROR: Database connection failed"')
        print('  python -m log_monitor_agent "WARNING: Memory usage at 85%"')
        print('  python -m log_monitor_agent "INFO: Application started"')
        sys.exit(1)

    log_message = " ".join(sys.argv[1:])
    print(f"Input: {log_message}")
    print("-" * 60)

    process_log_message(log_message)


if __name__ == "__main__":
    main()
