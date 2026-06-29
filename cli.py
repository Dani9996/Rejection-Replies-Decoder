#!/usr/bin/env python3
"""
Command-line interface for the Job Rejection Email Detector.

Usage:
    python cli.py "<email text>"          # analyze a string
    python cli.py -f email.txt            # analyze a file
    cat email.txt | python cli.py         # analyze piped stdin
    python cli.py -f email.txt --json     # machine-readable output
"""

import sys
import json
import argparse

from detector import analyze


def read_input(args) -> str:
    if args.file:
        with open(args.file, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    if args.text:
        return args.text
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("No input. Provide text, -f FILE, or pipe via stdin.")


def render(a) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append(" JOB REJECTION EMAIL ANALYSIS")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f" Automated / templated : {a.label(a.automated_score).upper():<12} "
                 f"(score {a.automated_score:.2f})")
    lines.append(f" AI-generated          : {a.label(a.ai_score).upper():<12} "
                 f"(score {a.ai_score:.2f})")
    lines.append("")
    if a.automated_hits:
        lines.append(" Automation signals found:")
        for h in a.automated_hits:
            lines.append(f"   - {h}")
        lines.append("")
    if a.ai_hits:
        lines.append(" AI-style signals found:")
        for h in a.ai_hits:
            lines.append(f"   - {h}")
        lines.append("")
    if a.notes:
        lines.append(" Notes:")
        for n in a.notes:
            lines.append(f"   * {n}")
        lines.append("")
    lines.append(" Reminder: these are heuristic estimates, not proof of")
    lines.append(" authorship. Use as a guide only.")
    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description="Detect automated and AI-generated job rejection emails.")
    p.add_argument("text", nargs="?", help="Email text to analyze.")
    p.add_argument("-f", "--file", help="Path to a text file containing the email.")
    p.add_argument("--json", action="store_true", help="Output JSON instead of a report.")
    args = p.parse_args()

    email = read_input(args)
    a = analyze(email)

    if args.json:
        print(json.dumps({
            "automated_score": a.automated_score,
            "is_automated": a.is_automated,
            "ai_score": a.ai_score,
            "is_ai_generated": a.is_ai_generated,
            "automated_hits": a.automated_hits,
            "ai_hits": a.ai_hits,
            "notes": a.notes,
        }, indent=2))
    else:
        print(render(a))


if __name__ == "__main__":
    main()
