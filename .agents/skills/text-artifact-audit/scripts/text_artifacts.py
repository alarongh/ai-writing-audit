"""Inspect Unicode formatting characters and remove selected ones in a new copy."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import unicodedata


TEXT_SUFFIXES = {".txt", ".md", ".markdown"}
REVIEWABLE = {
    0x00AD: "line_break",
    0x200B: "line_break",
    0x2060: "line_break",
    0xFEFF: "zero_width_no_break_space",
}
BIDI = {0x061C, 0x200E, 0x200F, *range(0x202A, 0x202F), *range(0x2066, 0x206A)}
SPACES = {0x00A0, 0x1680, *range(0x2000, 0x200B), 0x202F, 0x205F, 0x3000}
LINES = re.compile(r"[^\r\n]*(?:\r\n|\r|\n|$)")


def artifact_kind(code):
    if code in REVIEWABLE:
        return REVIEWABLE[code]
    if code in SPACES:
        return "space"
    if code in BIDI:
        return "bidi_control"
    if code in {0x200C, 0x200D}:
        return "joiner"
    if 0xFE00 <= code <= 0xFE0F or 0xE0100 <= code <= 0xE01EF:
        return "variation_selector"
    if code == 0xE0001 or 0xE0020 <= code <= 0xE007F:
        return "tag"
    return None


def find_artifacts(text):
    for line, match in enumerate(LINES.finditer(text), start=1):
        for column, character in enumerate(match.group(), start=1):
            index = match.start() + column - 1
            code = ord(character)
            if index == 0 and code == 0xFEFF:
                continue
            kind = artifact_kind(code)
            if kind:
                code_point = f"U+{code:04X}"
                yield index, {
                    "id": f"{line}:{column}:{code_point}",
                    "line": line,
                    "column": column,
                    "code_point": code_point,
                    "name": unicodedata.name(character, "UNNAMED"),
                    "kind": kind,
                    "removable_after_review": code in REVIEWABLE,
                }


def require_text_path(path):
    if path.suffix.lower() not in TEXT_SUFFIXES:
        raise ValueError("expected a .txt, .md or .markdown path")


def write_new_copy(path, data):
    # Stage bytes beside the destination so publishing the copy is atomic.
    temporary = tempfile.NamedTemporaryFile(dir=path.parent, delete=False)
    staged = Path(temporary.name)
    try:
        with temporary:
            temporary.write(data)
        os.link(staged, path)
    finally:
        staged.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    scan = commands.add_parser("scan", help="report exact positions without editing")
    scan.add_argument("source", type=Path)
    clean = commands.add_parser("clean", help="remove selected positions in a new file")
    clean.add_argument("source", type=Path)
    clean.add_argument("output", type=Path)
    clean.add_argument("--sha256", required=True, help="original hash from scan")
    clean.add_argument("--remove", action="append", required=True, metavar="ID")
    args = parser.parse_args()

    try:
        require_text_path(args.source)
        original = args.source.read_bytes()
        digest = hashlib.sha256(original).hexdigest()
        text = original.decode("utf-8")
        if args.command == "scan":
            findings = [finding for _, finding in find_artifacts(text)]
            print(json.dumps({"sha256": digest, "findings": findings}, indent=2))
            return

        require_text_path(args.output)
        if digest != args.sha256.lower():
            raise ValueError("source changed since scan")
        removable = {
            finding["id"]: index for index, finding in find_artifacts(text)
            if finding["removable_after_review"]
        }
        selected = set(args.remove)
        unavailable = selected - removable.keys()
        if unavailable:
            raise ValueError(f"unknown or protected IDs: {', '.join(sorted(unavailable))}")

        indices = {removable[identifier] for identifier in selected}
        result = "".join(char for index, char in enumerate(text) if index not in indices)
        write_new_copy(args.output, result.encode("utf-8"))
        print(json.dumps({"output": str(args.output), "removed": len(indices)}))
    except (OSError, ValueError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    main()
