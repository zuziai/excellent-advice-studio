"""Check or link installed runtimes; this command never installs or downloads packages."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'book-review'))
from runtime_support import inspect_runtime


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Read-only dependency check.')
    args = parser.parse_args()
    try:
        report = inspect_runtime(ROOT, bootstrap=not args.check)
    except (OSError, RuntimeError) as error:
        report = {'ready': False, 'networkUsed': False, 'error': str(error)}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report.get('ready') else 1)
