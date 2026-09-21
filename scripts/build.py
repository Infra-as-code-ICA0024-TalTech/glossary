#!/usr/bin/env python3
"""Build or validate the standalone ICA0024 glossary exports."""
import argparse
import json
from pathlib import Path

from glossary import build_glossary

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true',
                        help='Validate existing exports against the Markdown source without rebuilding')
    args = parser.parse_args()
    report = build_glossary(ROOT, check=args.check)
    (ROOT/'docs').mkdir(exist_ok=True)
    (ROOT/'docs/validation.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
