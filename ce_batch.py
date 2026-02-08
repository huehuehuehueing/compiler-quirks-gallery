#!/usr/bin/env python3
# Copyright (c) 2026 Larry H <l.gr [at] dartmouth [dot] edu>
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Compiler Optimization Gallery
# Developed for COSC-69.16: Basics of Reverse Engineering
# Dartmouth College, Winter 2026

"""
ce_batch.py

Batch-run Compiler Explorer + Claude Explain over a src/ tree using a YAML config.

YAML format (example):

scenarios:
  O3:
    flags: "-O3"
  O2:
    flags: "-O2"

compilers:
  - avrg1520
  - cg152
  - clang1910
  ...

Behavior:
- Validates compiler IDs against https://godbolt.org/api/compilers (or chosen CE base URL).
- Output directory structure:
    <out>/
      README.md
      <compiler-id>/                # upper level matches compiler "slug" (id)
        README.md
        <scenario>/                 # e.g. O2, O3
          <relpath-under-src>/      # mirrors src structure
            <stem>.src.c
            <stem>.compile.request.json
            <stem>.compile.response.json
            <stem>.asm
            <stem>.explain.request.json
            <stem>.explain.response.json
            <stem>.explain.md

Requirements:
- pyyaml: pip install pyyaml
- requests
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import yaml  # type: ignore
except Exception as e:
    raise SystemExit("Missing dependency: pyyaml. Install with: pip install pyyaml") from e

from ce_client import CompilerExplorerClient, CEError, ProgressInfo, process_source_tree


@dataclass(frozen=True)
class Scenario:
    name: str
    flags: str


class ProgressTracker:
    """Tracks progress and calculates ETA based on rolling average."""

    def __init__(self, total_operations: int):
        self.total = total_operations
        self.completed = 0
        self.start_time = time.time()
        self.step_times: List[float] = []
        self.last_step_time = self.start_time
        self.max_samples = 20  # Rolling average window

    def record_step(self) -> None:
        """Record completion of a step (compile or explain)."""
        now = time.time()
        elapsed = now - self.last_step_time
        self.step_times.append(elapsed)
        if len(self.step_times) > self.max_samples:
            self.step_times.pop(0)
        self.last_step_time = now

    def increment(self) -> None:
        """Increment completed count (after both compile + explain for a file)."""
        self.completed += 1

    def get_eta_str(self) -> str:
        """Calculate ETA based on average step time."""
        if not self.step_times:
            return "calculating..."

        avg_step_time = sum(self.step_times) / len(self.step_times)
        # Each file has 2 steps (compile + explain)
        remaining_files = self.total - self.completed
        remaining_steps = remaining_files * 2
        remaining_seconds = avg_step_time * remaining_steps

        if remaining_seconds < 60:
            return f"{int(remaining_seconds)}s"
        elif remaining_seconds < 3600:
            mins = int(remaining_seconds // 60)
            secs = int(remaining_seconds % 60)
            return f"{mins}m {secs}s"
        else:
            hours = int(remaining_seconds // 3600)
            mins = int((remaining_seconds % 3600) // 60)
            return f"{hours}h {mins}m"

    def get_elapsed_str(self) -> str:
        """Get elapsed time string."""
        elapsed = time.time() - self.start_time
        if elapsed < 60:
            return f"{int(elapsed)}s"
        elif elapsed < 3600:
            mins = int(elapsed // 60)
            secs = int(elapsed % 60)
            return f"{mins}m {secs}s"
        else:
            hours = int(elapsed // 3600)
            mins = int((elapsed % 3600) // 60)
            return f"{hours}h {mins}m"


def detect_instruction_set(compiler_id: str) -> str:
    """Detect instruction set architecture from compiler ID."""
    cid = compiler_id.lower()

    if "avr" in cid:
        return "avr"
    if "arm64" in cid or "aarch64" in cid or "armv8" in cid:
        return "aarch64"
    if "arm" in cid:
        return "arm32"
    if "mips64" in cid:
        return "mips64"
    if "mips" in cid:
        return "mips"
    if "sparc64" in cid:
        return "sparc64"
    if "sparc" in cid:
        return "sparc"
    if "riscv64" in cid or "rv64" in cid:
        return "riscv64"
    if "riscv" in cid or "rv32" in cid:
        return "riscv32"
    if "powerpc64" in cid or "ppc64" in cid:
        return "powerpc64"
    if "powerpc" in cid or "ppc" in cid:
        return "powerpc"
    if "x86" in cid or "i386" in cid or "i686" in cid:
        return "x86"
    # Default to amd64 for most x86-64 compilers (gcc, clang, msvc, mingw)
    return "amd64"


def format_progress(info: ProgressInfo, tracker: ProgressTracker) -> str:
    """Format progress information for display."""
    pct = (info.current / info.total * 100) if info.total > 0 else 0
    eta = tracker.get_eta_str()
    elapsed = tracker.get_elapsed_str()

    # [compiler][scenario][source] step (current/total) pct% | elapsed | ETA: eta
    return (
        f"[{info.compiler_id}][{info.scenario}][{info.source_file}] "
        f"{info.step:7s} ({info.current}/{info.total}) {pct:5.1f}% | "
        f"elapsed: {elapsed} | ETA: {eta}"
    )


def load_config_yaml(path: Path) -> Tuple[List[Scenario], List[str]]:
    obj = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise CEError("YAML root must be a mapping/object")

    scenarios_raw = obj.get("scenarios")
    compilers_raw = obj.get("compilers")

    if not isinstance(scenarios_raw, dict) or not scenarios_raw:
        raise CEError("YAML must contain non-empty 'scenarios' mapping")
    if not isinstance(compilers_raw, list) or not compilers_raw:
        raise CEError("YAML must contain non-empty 'compilers' list")

    scenarios: List[Scenario] = []
    for name, spec in scenarios_raw.items():
        if not isinstance(name, str):
            raise CEError("Scenario keys must be strings")
        if not isinstance(spec, dict):
            raise CEError(f"Scenario '{name}' must be a mapping with 'flags'")
        flags = spec.get("flags")
        if not isinstance(flags, str):
            raise CEError(f"Scenario '{name}' must have string 'flags'")
        scenarios.append(Scenario(name=name, flags=flags))

    compilers: List[str] = []
    for c in compilers_raw:
        if not isinstance(c, str):
            raise CEError("All 'compilers' entries must be strings (compiler IDs)")
        compilers.append(c)

    return scenarios, compilers


def validate_compilers_exist(client: CompilerExplorerClient, requested: List[str]) -> Set[str]:
    """
    Fetches /api/compilers and verifies requested IDs exist.

    Returns the set of valid compiler IDs (intersection). Raises if any are missing.
    """
    print("Validating compiler IDs...", end=" ", flush=True)
    all_compilers = client.get_compilers()
    all_ids: Set[str] = set()
    for item in all_compilers:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            all_ids.add(item["id"])

    missing = [c for c in requested if c not in all_ids]
    if missing:
        print("FAILED")
        raise CEError(
            "These compiler IDs were not found on this CE instance:\n"
            + "\n".join(f"  - {m}" for m in missing)
            + "\n\nCheck the instance's /api/compilers output or use a different --ce-base-url."
        )
    print(f"OK ({len(requested)} compilers)")
    return set(requested)


def count_source_files(src_root: Path, extensions: Tuple[str, ...]) -> int:
    """Count the total number of source files to process."""
    return len([p for p in src_root.rglob("*") if p.is_file() and p.suffix in extensions])


def write_top_index_readme(out_root: Path, scenarios: List[Scenario], compilers: List[str]) -> None:
    out_root.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    lines.append("# Compiler Explorer batch outputs\n")
    lines.append("## Scenarios\n")
    for sc in scenarios:
        lines.append(f"- **{sc.name}**: `{sc.flags}`")
    lines.append("")
    lines.append("## Compilers\n")
    lines.append("| Compiler ID | Link |")
    lines.append("|---|---|")
    for cid in compilers:
        lines.append(f"| `{cid}` | [{cid}](./{cid}/README.md) |")
    lines.append("")
    (out_root / "README.md").write_text("\n".join(lines), encoding="utf-8")


def write_compiler_readme(compiler_root: Path, compiler_id: str, scenarios: List[Scenario]) -> None:
    compiler_root.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    lines.append(f"# {compiler_id}\n")
    lines.append("## Scenarios\n")
    lines.append("| Scenario | Flags | Link |")
    lines.append("|---|---|---|")
    for sc in scenarios:
        lines.append(f"| `{sc.name}` | `{sc.flags}` | [{sc.name}](./{sc.name}/) |")
    lines.append("")
    (compiler_root / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Batch-run Compiler Explorer + Claude Explain over source files"
    )
    ap.add_argument("--yaml", required=True, help="Path to YAML config")
    ap.add_argument("--src", required=True, help="Path to src directory root (contains subfolders/files)")
    ap.add_argument("--out", required=True, help="Output directory root")
    ap.add_argument("--ce-base-url", default="https://godbolt.org", help="Compiler Explorer base URL")
    ap.add_argument("--explain-base-url", default="https://api.compiler-explorer.com/explain", help="Explain base URL")
    ap.add_argument("--lang", default=None, help="Optional CE language id (e.g., 'c', 'c++')")
    ap.add_argument("--explain-language", default="c", help="Explain API language field (e.g., c, c++)")
    ap.add_argument("--explain-compiler", default="unknown", help="Human compiler string for explain payload")
    ap.add_argument("--instruction-set", default="amd64", help="Explain instructionSet (e.g., amd64)")
    ap.add_argument("--audience", default="beginner", choices=["beginner", "experienced"])
    ap.add_argument("--explain-type", default="assembly", choices=["assembly", "haiku"])
    ap.add_argument("--sleep", type=float, default=0.0, help="Sleep between files (seconds)")
    ap.add_argument("--bypass-compile-cache", type=int, default=0, help="0/1/2 bypassCache enum for CE compile")
    ap.add_argument("--bypass-explain-cache", action="store_true", help="Bypass Explain caches")
    ap.add_argument(
        "--extensions",
        default=".c,.cc,.cpp,.cxx,.C,.h,.hpp",
        help="Comma-separated extensions to include",
    )
    ap.add_argument("-q", "--quiet", action="store_true", help="Suppress progress output")
    args = ap.parse_args()

    yaml_path = Path(args.yaml)
    src_root = Path(args.src)
    out_root = Path(args.out)
    exts = tuple(e.strip() for e in args.extensions.split(",") if e.strip())

    print(f"Loading config from {yaml_path}...")
    scenarios, compilers = load_config_yaml(yaml_path)
    print(f"  {len(scenarios)} scenarios, {len(compilers)} compilers")

    client = CompilerExplorerClient(
        ce_base_url=args.ce_base_url,
        explain_base_url=args.explain_base_url,
    )

    # Validate compiler IDs exist on this CE instance.
    validate_compilers_exist(client, compilers)

    # Count total files for progress tracking
    num_files = count_source_files(src_root, exts)
    total_operations = num_files * len(compilers) * len(scenarios)
    print(f"Found {num_files} source files")
    print(f"Total: {total_operations} file compilations ({num_files} files x {len(compilers)} compilers x {len(scenarios)} scenarios)")
    print()

    # Top-level README
    write_top_index_readme(out_root, scenarios, compilers)

    # Progress tracker
    tracker = ProgressTracker(total_operations)
    last_line_len = 0

    def progress_callback(info: ProgressInfo) -> None:
        nonlocal last_line_len
        if args.quiet:
            return

        tracker.record_step()
        line = format_progress(info, tracker)

        # Clear previous line and print new one
        sys.stdout.write("\r" + " " * last_line_len + "\r")
        sys.stdout.write(line)
        sys.stdout.flush()
        last_line_len = len(line)

    # Run per compiler, per scenario
    file_index = 0
    for compiler_id in compilers:
        compiler_out = out_root / compiler_id
        write_compiler_readme(compiler_out, compiler_id, scenarios)

        for sc in scenarios:
            scenario_out = compiler_out / sc.name

            explain_compiler_label = args.explain_compiler if args.explain_compiler != "unknown" else compiler_id

            files_processed = process_source_tree(
                src_root=src_root,
                out_root=scenario_out,
                client=client,
                compiler_id=compiler_id,
                scenario_name=sc.name,
                ce_lang_id=args.lang,
                ce_user_arguments=sc.flags,
                explain_language=args.explain_language,
                explain_compiler_human=explain_compiler_label,
                instruction_set=detect_instruction_set(compiler_id),
                explain_audience=args.audience,
                explain_type=args.explain_type,
                bypass_compile_cache=args.bypass_compile_cache,
                bypass_explain_cache=args.bypass_explain_cache,
                extensions=exts,
                sleep_s=args.sleep,
                progress_callback=progress_callback,
                file_index_offset=file_index,
                total_files_global=total_operations,
            )

            file_index += files_processed
            tracker.completed = file_index

    # Final newline after progress
    if not args.quiet:
        print()
        print()
        print(f"Completed {total_operations} compilations in {tracker.get_elapsed_str()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
