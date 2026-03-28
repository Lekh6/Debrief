import requests


def main() -> None:
    response = requests.options(
        "http://127.0.0.1:8003/api/v1/meetings/extract",
        headers={
            "Origin": "http://127.0.0.1:4179",
            "Access-Control-Request-Method": "POST",
        },
        timeout=20,
    )
    print("status:", response.status_code)
    print("allow-origin:", response.headers.get("access-control-allow-origin"))
    print("allow-methods:", response.headers.get("access-control-allow-methods"))


if __name__ == "__main__":
    main()
