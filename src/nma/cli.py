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
from .extraction import extract_pdf_candidates, write_jsonl
from .knowledge import PortrayalGraph, compile_portrayal_graph
from .portrayal import PortrayalAgent, compile_maplibre_layers
from .demo_contract import check_demo_contract, reset_demo_contract
from .demo_freeze import check_demo_freeze
from .demo_offline import check_offline_runtime
from .demo_soak import run_demo_soak


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
    server.add_argument("--graph", default="data/knowledge/portrayal-graph.json")

    inspect = sub.add_parser("inspect", help="inspect a vector dataset with GDAL/OGR")
    inspect.add_argument("dataset")

    extract = sub.add_parser(
        "extract-portrayal", help="extract code-anchored review candidates from a portrayal PDF"
    )
    extract.add_argument("--pdf", required=True)
    extract.add_argument("--out", required=True)

    compile_graph = sub.add_parser(
        "compile-knowledge", help="compile reviewed PDF records into executable graph knowledge"
    )
    compile_graph.add_argument("--records", default="data/extraction/portrayal-records.jsonl")
    compile_graph.add_argument("--profile", default="data/knowledge/portrayal-profile.json")
    compile_graph.add_argument("--out", default="data/knowledge/portrayal-graph.json")

    ask = sub.add_parser("ask", help="answer a human portrayal question through GraphRAG")
    ask.add_argument("question")
    ask.add_argument("--graph", default="data/knowledge/portrayal-graph.json")

    portray = sub.add_parser("portray", help="select a symbol through the executable graph")
    portray.add_argument("feature_code")
    portray.add_argument("--scale", type=int, default=1000)
    portray.add_argument("--profile-id")
    portray.add_argument("--large-detached-building", action="store_true")
    portray.add_argument("--graph", default="data/knowledge/portrayal-graph.json")

    style = sub.add_parser("compile-style", help="compile graph rules to MapLibre style layers")
    style.add_argument("--graph", default="data/knowledge/portrayal-graph.json")
    style.add_argument("--out", default="artifacts/portrayal/maplibre-layers.json")

    demo_scenes = sub.add_parser(
        "demo-scenes", help="check or reset the frozen five-scene RC1 demo contract"
    )
    demo_scenes.add_argument("--contract", default="data/demo/five-scene-demo.json")
    demo_scenes.add_argument("--reset", action="store_true")

    demo_freeze = sub.add_parser(
        "demo-freeze", help="verify the feature-complete five-scene demo manifest"
    )
    demo_freeze.add_argument("--manifest", default="data/demo/five-scene-freeze.json")

    demo_soak = sub.add_parser(
        "demo-soak", help="repeat the frozen five-scene sequence from clean resets"
    )
    demo_soak.add_argument("--contract", default="data/demo/five-scene-demo.json")
    demo_soak.add_argument("--freeze", default="data/demo/five-scene-freeze.json")
    demo_soak.add_argument("--iterations", type=int, default=20)
    demo_soak.add_argument("--output", default="artifacts/soak/five-scene-soak.json")

    demo_offline = sub.add_parser(
        "demo-offline", help="verify local assets, runtime caching, and degraded fallback"
    )
    demo_offline.add_argument("--manifest", default="data/demo/offline-runtime.json")
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
        serve(
            Specification.load(resolve_asset(args.spec)),
            args.host,
            args.port,
            PortrayalGraph.load(resolve_asset(args.graph)),
        )
        return 0

    if args.command == "inspect":
        result = inspect_dataset(resolve_asset(args.dataset))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["available"] else 2

    if args.command == "extract-portrayal":
        candidates = extract_pdf_candidates(resolve_asset(args.pdf))
        write_jsonl(candidates, Path(args.out))
        print(f"Extracted {len(candidates)} review candidates to {Path(args.out).resolve()}")
        return 0

    if args.command == "compile-knowledge":
        graph = compile_portrayal_graph(resolve_asset(args.records), resolve_asset(args.profile))
        dump_json(graph, args.out)
        print(
            f"Compiled {graph['statistics']['observations']} reviewed PDF observations into "
            f"{graph['statistics']['nodes']} nodes and {graph['statistics']['edges']} edges."
        )
        return 0

    if args.command == "ask":
        answer = PortrayalAgent(PortrayalGraph.load(resolve_asset(args.graph))).answer(
            args.question
        )
        print(json.dumps(answer, ensure_ascii=False, indent=2))
        return 0 if answer["status"] == "answered" else 2

    if args.command == "portray":
        decision = PortrayalAgent(PortrayalGraph.load(resolve_asset(args.graph))).select_symbol(
            args.feature_code,
            scale_denominator=args.scale,
            profile_id=args.profile_id,
            attributes={"large_detached_building": args.large_detached_building},
        )
        print(json.dumps(decision.as_dict(), ensure_ascii=False, indent=2))
        return 0 if decision.status == "selected" else 2

    if args.command == "compile-style":
        graph = PortrayalGraph.load(resolve_asset(args.graph))
        layers = compile_maplibre_layers(graph)
        dump_json({"version": 8, "layers": layers}, args.out)
        print(f"Compiled {len(layers)} evidence-bearing MapLibre layers.")
        return 0

    if args.command == "demo-scenes":
        result = (
            reset_demo_contract(args.contract) if args.reset else check_demo_contract(args.contract)
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "demo-freeze":
        result = check_demo_freeze(args.manifest)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "demo-soak":
        result = run_demo_soak(
            args.contract,
            args.freeze,
            iterations=args.iterations,
            output=args.output,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["summary"]["failed"] == 0 else 2

    if args.command == "demo-offline":
        result = check_offline_runtime(args.manifest)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

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
