"""Download official Malaysian public datasets used in the analysis."""

from pathlib import Path
import requests

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

SOURCES = {
    "hies_state.csv": "https://storage.dosm.gov.my/hies/hies_state.csv",
    "hh_income_state.csv": "https://storage.dosm.gov.my/hies/hh_income_state.csv",
    "cpi_state.csv": "https://storage.dosm.gov.my/cpi/cpi_2d_state.csv",
    "formal_wages_state.csv": "https://storage.dosm.gov.my/labour/formal_wages_state.csv",
}

def download(url: str, destination: Path) -> None:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    destination.write_bytes(response.content)

def main() -> None:
    for filename, url in SOURCES.items():
        destination = RAW_DIR / filename
        print(f"Downloading {filename} ...")
        download(url, destination)
        print(f"Saved: {destination}")

if __name__ == "__main__":
    main()
