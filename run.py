"""Start the Card Nova server:  python run.py  [--reseed] [--port 5000]"""
import argparse

from backend import create_app

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--reseed", action="store_true", help="reload the card catalogue from seed_data.py")
    args = parser.parse_args()
    create_app(reseed=args.reseed).run(host="127.0.0.1", port=args.port, debug=True)
