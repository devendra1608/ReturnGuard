
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "raw" / "olist"


def inspect_csv(path: Path) -> None:
    """Inspect a CSV without loading the entire file into memory."""

    print(f"\n{'=' * 70}")
    print(f"File: {path.name}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        print("Columns:", reader.fieldnames)

        row_count = 0
        examples = []

        for row in reader:
            row_count += 1

            if len(examples) < 2:
                examples.append(row)

    print("Rows:", row_count)

    for index, example in enumerate(examples, start=1):
        print(f"\nExample {index}:")
        for key, value in example.items():
            print(f"  {key}: {value}")


def main() -> None:
    if not DATA_DIR.exists():
        raise FileNotFoundError(
            f"Dataset directory not found: {DATA_DIR}"
        )

    csv_files = sorted(DATA_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {DATA_DIR}"
        )

    print(f"Inspecting {len(csv_files)} CSV files")
    print(f"Dataset directory: {DATA_DIR}")

    for path in csv_files:
        inspect_csv(path)

    print("\nInspection completed.")


if __name__ == "__main__":
    main()
