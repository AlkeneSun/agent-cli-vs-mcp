import argparse
import json
import sys
from amap_api import search_poi

def main():
    parser = argparse.ArgumentParser(description="Amap POI Search Tool CLI")
    parser.add_argument("--keywords", type=str, required=True, help="Keywords to search")
    parser.add_argument("--city", type=str, default="", help="City to search in")
    parser.add_argument("--force_error", type=str, default="", help="Mock error message")
    
    try:
        args = parser.parse_args()
    except SystemExit:
        # Prevent argparse from directly sys.exit() and printing to stderr in a way that breaks JSON wrap
        # But for CLI mode, printing to stderr is expected. We just let it exit.
        sys.exit(1)

    res = search_poi(args.keywords, args.city, force_error=args.force_error)
    print(json.dumps(res, ensure_ascii=False))
    sys.exit(0 if res.get("status", "") == "success" else 1)

if __name__ == "__main__":
    main()
