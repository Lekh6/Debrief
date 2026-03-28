import json
import urllib.request


def fetch(url: str) -> str:
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.read().decode()


def main() -> None:
    health = fetch("http://127.0.0.1:8001/health")
    projects = json.loads(fetch("http://127.0.0.1:8001/api/v1/projects"))
    homepage = fetch("http://127.0.0.1:4174")

    print("health:", health)
    print("projects:", len(projects))
    print("homepage_has_root:", "<div id=\"root\"></div>" in homepage)


if __name__ == "__main__":
    main()
