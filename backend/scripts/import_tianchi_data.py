import argparse
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.data_importer import import_tianchi_dataset


def main():
    parser = argparse.ArgumentParser(description="Import Tianchi jobs/candidates/applications CSV data.")
    parser.add_argument(
        "--data-dir",
        default=r"D:\caogao6\岗位数据",
        help="Directory containing jobs.csv, candidates.csv and applications.csv.",
    )
    parser.add_argument("--reset", action="store_true", help="Clear core tables before import.")
    args = parser.parse_args()

    summary = import_tianchi_dataset(args.data_dir, reset=args.reset)
    print("Tianchi data import complete:")
    for name, count in summary.items():
        print(f"  {name}: {count}")


if __name__ == "__main__":
    main()
