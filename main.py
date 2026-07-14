"""
Application entry point.
"""

from app import startup

from config import settings


def main() -> None:
    """
    Main application entry point.
    """

    startup()

    print("=" * 60)
    print(settings.APP_NAME)
    print("=" * 60)

    print("Application Ready")


if __name__ == "__main__":
    main()