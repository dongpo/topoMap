from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .demo import run_demo
from .api import serve
from .io import dump_json
from .ogr import inspect_dataset
from .paths import resolve_asset
from .report import render_html
from .specification import Specification
from .validator import Validator
from .versioning import compare_specifications


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nma", description="National Map Agent reference CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate a GeoJSON dataset against a specification")
    validate.add_argument("--spec", required=True)
    validate.add_argument("--dataset", required=True)
    validate.add_argument("--json-out")
    validate.add_argument("--html-out")

    rules = sub.add_parser("rules", help="list executable rules and their evidence")
    rules.add_argument("--spec", required=True)

    demo = sub.add_parser("demo", help="run the end-to-end validation and repair workflow")
    demo.add_argument("--spec", default="data/specifications/taiwan-5000-riverl-112.json")
    demo.add_argument(
        "--dataset", default="data/datasets/authoritative/riverl-defective/RIVERL.shp"
    )
    demo.add_argument("--output", default="artifacts/demo")
    demo.add_argument("--approve-safe-repairs", action="store_true")

    compare = sub.add_parser("compare", help="compare two machine-readable specification versions")
    compare.add_argument("--old", required=True)
    compare.add_argument("--new", required=True)

    server = sub.add_parser("serve", help="serve the dependency-free JSON API")
    server.add_argument("--spec", default="data/specifications/taiwan-5000-riverl-112.json")
    server.add_argument("--host", default="127.0.0.1")
    server.add_argument("--port", type=int, default=8000)

    inspect = sub.add_parser("inspect", help="inspect a vector dataset with GDAL/OGR")
    inspect.add_argument("dataset")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "rules":
        specification = Specification.load(resolve_asset(args.spec))
        print(
            json.dumps(
                [rule.as_dict() for rule in specification.rules], ensure_ascii=False, indent=2
            )
        )
        return 0

    if args.command == "compare":
        result = compare_specifications(
            Specification.load(resolve_asset(args.old)),
            Specification.load(resolve_asset(args.new)),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "serve":
        serve(Specification.load(resolve_asset(args.spec)), args.host, args.port)
        return 0

    if args.command == "inspect":
        result = inspect_dataset(resolve_asset(args.dataset))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["available"] else 2

    if args.command == "validate":
        specification = Specification.load(resolve_asset(args.spec))
        validator = Validator(specification)
        dataset = resolve_asset(args.dataset)
        report = validator.validate_path(dataset)
        if args.json_out:
            dump_json(report, args.json_out)
        if args.html_out:
            from .ogr import read_vector_dataset

            collection, _ = read_vector_dataset(dataset)
            render_html(report, collection, args.html_out)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if report["status"] == "failed" else 0

    result = run_demo(
        resolve_asset(args.spec),
        resolve_asset(args.dataset),
        args.output,
        approve_safe_repairs=args.approve_safe_repairs,
    )
    before = result["before"]["summary"]
    error_word = "error" if before["errors"] == 1 else "errors"
    warning_word = "warning" if before["warnings"] == 1 else "warnings"
    print(f"Before: {before['errors']} {error_word}, {before['warnings']} {warning_word}")
    print(f"Repair proposals: {len(result['repair_plan'])}")
    if result["after"]:
        after = result["after"]["summary"]
        after_error_word = "error" if after["errors"] == 1 else "errors"
        after_warning_word = "warning" if after["warnings"] == 1 else "warnings"
        print(f"Approved repairs applied: {len(result['repairs_applied'])}")
        print(
            f"After: {after['errors']} {after_error_word}, {after['warnings']} {after_warning_word}"
        )
    else:
        print("No repair executed. Re-run with --approve-safe-repairs to approve safe changes.")
    print(f"Artifacts: {Path(args.output).resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
