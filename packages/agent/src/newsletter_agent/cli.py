from __future__ import annotations
import argparse
import asyncio
import json
from pathlib import Path
from typing import List

from .types import Subscription, Candidate, AgentState
from .llm_ops import generate_newsletter_content


def _read_input_json(path: Path) -> tuple[Subscription, List[Candidate]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    sub = Subscription(**data["subscription"])  # may raise ValidationError
    candidates = [Candidate(**c) for c in data.get("candidates", [])]
    return sub, candidates


async def _generate(input_path: Path, out_dir: Path) -> int:
    sub, candidates = _read_input_json(input_path)
    state: AgentState = {}

    selected, newsletter = await generate_newsletter_content(sub, candidates, state)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "newsletter.html").write_text(newsletter.html, encoding="utf-8")
    (out_dir / "newsletter.txt").write_text(newsletter.text, encoding="utf-8")

    print("Generated:")
    print(f"- HTML: {out_dir / 'newsletter.html'}")
    print(f"- Text: {out_dir / 'newsletter.txt'}")

    if state.get("errors"):
        print("Warnings/Errors:")
        for e in state["errors"]:
            print(f"- {e.source}:{e.code} - {e.message}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="newsletter-agent",
        description="Generate a newsletter locally using Azure OpenAI and input JSON.",
    )
    subp = p.add_subparsers(dest="cmd", required=True)

    gen = subp.add_parser(
        "generate",
        help="Generate newsletter files (HTML & text) from an input JSON file.",
    )
    gen.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Path to input JSON containing 'subscription' and 'candidates'.",
    )
    gen.add_argument(
        "--out",
        "-o",
        type=Path,
        default=Path("dist"),
        help="Output directory (default: ./dist)",
    )

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.cmd == "generate":
        try:
            exit_code = asyncio.run(_generate(args.input, args.out))
        except KeyboardInterrupt:
            exit_code = 130
        except Exception as e:
            # Keep errors concise for CLI usage
            print(f"Error: {e}")
            exit_code = 1
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
