#!/usr/bin/env python3
import argparse
import sys
import json
from amap_api import search_poi

def create_parser():
    parser = argparse.ArgumentParser(
        prog="amap-cli",
        description="Amap Agent-Native CLI: Composable location services for the Unix terminal.\n"
                    "Output is always raw JSON for easy pipelining with tools like jq.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Search POI
    search_parser = subparsers.add_parser("search", help="Search Points of Interest (POI). eg: amap-cli search --keywords 'coffee' | jq '.data[0]'")
    search_parser.add_argument("--keywords", "-k", required=True, help="Search keywords (e.g., 'Starbucks', 'Hospital')")
    search_parser.add_argument("--city", "-c", default="", help="City context (e.g., 'Beijing')")
    search_parser.add_argument("--limit", type=int, default=3, help="Result limit")

    # Route (Mocked for schema size padding)
    route_parser = subparsers.add_parser("route", help="Plan a driving or walking route.")
    route_parser.add_argument("--origin", required=True, help="Origin coords (lng,lat)")
    route_parser.add_argument("--destination", required=True, help="Dest coords (lng,lat)")
    route_parser.add_argument("--strategy", choices=["fastest", "shortest", "avoid_highway"], default="fastest", help="Routing strategy")

    # Map Extract (Mocked for schema size padding)
    map_parser = subparsers.add_parser("map", help="Extract static map image url.")
    map_parser.add_argument("--center", required=True, help="Center coords (lng,lat)")
    map_parser.add_argument("--zoom", type=int, default=10, help="Zoom level 1-17")
    map_parser.add_argument("--size", default="400*400", help="Resolution width*height")

    return parser

def main():
    parser = create_parser()
    
    # Custom help interception to mimic Agent discovery
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
        
    args = parser.parse_args()

    if args.command == "search":
        res = search_poi(args.keywords, args.city, offset=args.limit)
        # Unix Philosophy: emit raw valid JSON to stdout so it can be piped.
        # No extra human readable logging unless printed to stderr.
        print(json.dumps(res, ensure_ascii=False))
        sys.exit(0 if res.get("status") == "success" else 1)
        
    elif args.command == "route":
        print(json.dumps({"status": "success", "data": {"distance": 5000, "duration": 1800, "steps": ["Turn left", "Go straight"]}}))
    elif args.command == "map":
        print(json.dumps({"status": "success", "url": "https://restapi.amap.com/v3/staticmap?mock=1"}))

if __name__ == "__main__":
    main()
