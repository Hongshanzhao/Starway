import argparse
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.db_cleanup import cleanup_unused_tables


def main():
    parser = argparse.ArgumentParser(description="Audit or clean Starway SQLite runtime tables.")
    parser.add_argument("--apply", action="store_true", help="Actually drop candidate legacy tables.")
    parser.add_argument("--purge-data", action="store_true", help="Delete runtime/cache rows but keep table schemas.")
    args = parser.parse_args()
    result = cleanup_unused_tables(apply=args.apply, purge_data=args.purge_data)
    print("Protected tables:")
    for table in result["protected"]:
        print(f"  {table}")
    print("Cleanup candidates:")
    for table in result["candidates"]:
        print(f"  {table}")
    print("Data purge candidates:")
    for table in result["purge_candidates"]:
        print(f"  {table}")
    if args.apply:
        print("Purged tables:")
        for table in result["purged"]:
            print(f"  {table}")
        print("Dropped tables:")
        for table in result["dropped"]:
            print(f"  {table}")
    else:
        print("Dry run only. Re-run with --apply and optional --purge-data to clean candidates.")


if __name__ == "__main__":
    main()
