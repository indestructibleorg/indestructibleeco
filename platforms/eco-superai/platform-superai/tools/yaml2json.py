"""YAML to JSON converter with validation and batch support."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml


def convert_yaml_to_json(yaml_content: str, indent: int = 2) -> str:
    parsed = yaml.safe_load(yaml_content)
    return json.dumps(parsed, indent=indent, ensure_ascii=False, default=str)


def convert_file(input_path: str, output_path: str | None = None, indent: int = 2) -> str:
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {input_path}")

    with open(path) as f:
        content = f.read()

    # Handle multi-document YAML
    documents = list(yaml.safe_load_all(content))
    if len(documents) == 1:
        result = json.dumps(documents[0], indent=indent, ensure_ascii=False, default=str)
    else:
        result = json.dumps(documents, indent=indent, ensure_ascii=False, default=str)

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w") as f:
            f.write(result)

    return result


def validate_yaml(content: str) -> dict[str, Any]:
    try:
        documents = list(yaml.safe_load_all(content))
        return {
            "valid": True,
            "document_count": len(documents),
            "types": [type(d).__name__ for d in documents],
        }
    except yaml.YAMLError as e:
        return {"valid": False, "error": str(e)}


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="YAML to JSON converter")
    parser.add_argument("input", nargs="?", help="Input YAML file (or stdin)")
    parser.add_argument("-o", "--output", help="Output JSON file")
    parser.add_argument("--indent", type=int, default=2, help="JSON indent level")
    parser.add_argument("--validate", action="store_true", help="Validate YAML only")
    parser.add_argument("--batch", nargs="+", help="Batch convert multiple files")
    args = parser.parse_args()

    if args.batch:
        for filepath in args.batch:
            try:
                out = filepath.rsplit(".", 1)[0] + ".json"
                convert_file(filepath, out, args.indent)
                print(f"✅ {filepath} -> {out}")
            except Exception as e:
                print(f"❌ {filepath}: {e}")
        return

    if args.input:
        content = Path(args.input).read_text()
    else:
        content = sys.stdin.read()

    if args.validate:
        result = validate_yaml(content)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["valid"] else 1)

    if args.input:
        result = convert_file(args.input, args.output, args.indent)
    else:
        result = convert_yaml_to_json(content, args.indent)

    if not args.output:
        print(result)


if __name__ == "__main__":
    main()