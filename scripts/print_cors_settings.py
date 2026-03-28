from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    print(settings.cors_origins)


if __name__ == "__main__":
    main()
