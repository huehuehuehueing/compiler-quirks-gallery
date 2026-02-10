# Copyright (c) 2026 Larry H <l.gr [at] dartmouth [dot] edu>
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Compiler Optimization Gallery
# Developed for COSC-69.16: Basics of Reverse Engineering
# Dartmouth College, Winter 2026

from __future__ import annotations

import json
import re
import time
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple
import urllib.parse

import requests


class CEError(RuntimeError):
    pass


@dataclass
class GalleryHints:
    """Per-file hints parsed from ``/* @gallery-hints … */`` blocks."""
    extra_flags: str = ""
    replace_flags: Optional[str] = None
    compiler_only: Optional[Set[str]] = None
    compiler_exclude: Optional[Set[str]] = None
    scenario_only: Optional[Set[str]] = None
    scenario_exclude: Optional[Set[str]] = None

    def should_compile(self, compiler_id: str, scenario_name: str) -> bool:
        if self.compiler_only is not None and compiler_id not in self.compiler_only:
            return False
        if self.compiler_exclude is not None and compiler_id in self.compiler_exclude:
            return False
        if self.scenario_only is not None and scenario_name not in self.scenario_only:
            return False
        if self.scenario_exclude is not None and scenario_name in self.scenario_exclude:
            return False
        return True

    def effective_flags(self, base_flags: str) -> str:
        if self.replace_flags is not None:
            return self.replace_flags
        if self.extra_flags:
            return f"{base_flags} {self.extra_flags}".strip()
        return base_flags


_HINTS_BLOCK_RE = re.compile(
    r"/\*\s*@gallery-hints\b(.*?)\*/", re.DOTALL
)

_COMMA_SET_KEYS = {
    "compiler-only", "compiler-exclude", "scenario-only", "scenario-exclude",
}


def parse_gallery_hints(source: str) -> GalleryHints:
    """Parse a ``/* @gallery-hints … */`` block from C source text."""
    m = _HINTS_BLOCK_RE.search(source)
    if not m:
        return GalleryHints()

    hints = GalleryHints()
    for line in m.group(1).splitlines():
        line = line.strip().lstrip("*").strip()
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()
        if not value:
            continue

        if key == "extra-flags":
            hints.extra_flags = value
        elif key == "replace-flags":
            hints.replace_flags = value
        elif key in _COMMA_SET_KEYS:
            items = {v.strip() for v in value.split(",") if v.strip()}
            if key == "compiler-only":
                hints.compiler_only = items
            elif key == "compiler-exclude":
                hints.compiler_exclude = items
            elif key == "scenario-only":
                hints.scenario_only = items
            elif key == "scenario-exclude":
                hints.scenario_exclude = items

    return hints


@dataclass(frozen=True)
class ProgressInfo:
    """Progress information for a single file processing step."""
    compiler_id: str
    scenario: str
    source_file: str
    step: str  # "compile" or "explain"
    current: int
    total: int


@dataclass(frozen=True)
class CompileResult:
    request: Dict[str, Any]
    response: Dict[str, Any]
    asm_text: str


@dataclass(frozen=True)
class ExplainResult:
    request: Dict[str, Any]
    response: Dict[str, Any]
    explanation_md: str


class CompilerExplorerClient:
    """
    Client for Godbolt / Compiler Explorer REST API and Claude Explain.

    - CE REST endpoints live under /api/* and return JSON when Accept: application/json is set.
      See provided REST API documentation. :contentReference[oaicite:4]{index=4}
    - Compile endpoint: POST /api/compiler/<compiler-id>/compile with JSON payload.
      :contentReference[oaicite:5]{index=5}
    - Claude Explain endpoint: separate service (default https://api.compiler-explorer.com/explain).
      :contentReference[oaicite:6]{index=6}
    """

    def __init__(
        self,
        ce_base_url: str = "https://godbolt.org",
        explain_base_url: str = "https://api.compiler-explorer.com/explain",
        timeout_s: float = 60.0,
        user_agent: str = "ce-client/1.0",
    ) -> None:
        self.ce_base_url = ce_base_url.rstrip("/")
        self.explain_base_url = explain_base_url.rstrip("/")
        self.timeout_s = timeout_s

        self._ce = requests.Session()
        self._ce.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": user_agent,
            }
        )

        self._explain = requests.Session()
        self._explain.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": user_agent,
            }
        )

    # ---------------------------
    # CE REST API convenience
    # ---------------------------

    def get_languages(self) -> List[Dict[str, Any]]:
        url = f"{self.ce_base_url}/api/languages"
        r = self._ce.get(url, timeout=self.timeout_s)
        self._raise_for_status(r, "GET /api/languages")
        data = r.json()
        if not isinstance(data, list):
            raise CEError(f"Unexpected languages response type: {type(data)}")
        return data

    def get_compilers(self, language_id: Optional[str] = None, fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        if language_id:
            url = f"{self.ce_base_url}/api/compilers/{urllib.parse.quote(language_id)}"
        else:
            url = f"{self.ce_base_url}/api/compilers"

        params = {}
        if fields:
            params["fields"] = ",".join(fields)

        r = self._ce.get(url, params=params, timeout=self.timeout_s)
        self._raise_for_status(r, "GET /api/compilers")
        data = r.json()
        if not isinstance(data, list):
            raise CEError(f"Unexpected compilers response type: {type(data)}")
        return data

    def compile_to_asm(
        self,
        compiler_id: str,
        source: str,
        user_arguments: str = "-O2",
        lang: Optional[str] = None,
        intel_syntax: bool = True,
        demangle: bool = True,
        labels: bool = True,
        directives: bool = True,
        comment_only: bool = True,
        trim: bool = False,
        library_code: bool = False,
        bypass_cache: int = 0,
        tools: Optional[List[Dict[str, str]]] = None,
        libraries: Optional[List[Dict[str, str]]] = None,
        extra_files: Optional[List[Dict[str, str]]] = None,
    ) -> CompileResult:
        """
        Calls POST /api/compiler/<compiler-id>/compile with JSON payload. :contentReference[oaicite:7]{index=7}

        bypass_cache is the enum described in docs (0,1,2). :contentReference[oaicite:8]{index=8}
        """
        url = f"{self.ce_base_url}/api/compiler/{urllib.parse.quote(compiler_id)}/compile"

        payload: Dict[str, Any] = {
            "source": source,
            "options": {
                "userArguments": user_arguments,
                "compilerOptions": {
                    "skipAsm": False,
                    "executorRequest": False,
                    "overrides": [],
                },
                "filters": {
                    "binary": False,
                    "binaryObject": False,
                    "commentOnly": bool(comment_only),
                    "demangle": bool(demangle),
                    "directives": bool(directives),
                    "execute": False,
                    "intel": bool(intel_syntax),
                    "labels": bool(labels),
                    "libraryCode": bool(library_code),
                    "trim": bool(trim),
                    "debugCalls": False,
                },
                "tools": tools or [],
                "libraries": libraries or [],
                "executeParameters": {"args": [], "stdin": "", "runtimeTools": []},
            },
            "allowStoreCodeDebug": True,
            "bypassCache": int(bypass_cache),
        }
        if lang:
            payload["lang"] = lang
        if extra_files:
            # Multi-file support as described in docs. :contentReference[oaicite:9]{index=9}
            payload["files"] = extra_files

        r = self._ce.post(url, data=json.dumps(payload), timeout=self.timeout_s)
        self._raise_for_status(r, f"POST /api/compiler/{compiler_id}/compile")
        resp = r.json()

        asm_lines = resp.get("asm", [])
        asm_text = ""
        if isinstance(asm_lines, list):
            # JSON response format has asm lines as objects with "text". :contentReference[oaicite:10]{index=10}
            out_lines: List[str] = []
            for item in asm_lines:
                if isinstance(item, dict) and "text" in item:
                    out_lines.append(str(item["text"]))
            asm_text = "\n".join(out_lines).rstrip() + ("\n" if out_lines else "")
        else:
            asm_text = ""

        return CompileResult(request=payload, response=resp, asm_text=asm_text)

    # ---------------------------
    # Claude Explain
    # ---------------------------

    def explain_assembly(
        self,
        *,
        language: str,
        compiler: str,
        code: str,
        compilation_options: List[str],
        instruction_set: str,
        asm_lines: List[Dict[str, str]],
        audience: str = "beginner",
        explanation_type: str = "assembly",
        bypass_cache: bool = False,
    ) -> ExplainResult:
        """
        Calls Claude Explain POST / with payload described in ClaudeExplain.md. :contentReference[oaicite:11]{index=11}
        """
        url = f"{self.explain_base_url}/"

        payload: Dict[str, Any] = {
            "language": language,
            "compiler": compiler,
            "code": code,
            "compilationOptions": compilation_options,
            "instructionSet": instruction_set,
            "asm": asm_lines,
            "audience": audience,
            "explanation": explanation_type,
            "bypassCache": bool(bypass_cache),
        }

        r = self._explain.post(url, data=json.dumps(payload), timeout=self.timeout_s)
        self._raise_for_status(r, "POST explain /")
        resp = r.json()

        explanation_md = ""
        if isinstance(resp, dict) and resp.get("status") == "success":
            explanation_md = str(resp.get("explanation", ""))
        else:
            # Keep an explicit failure body around; caller can inspect response JSON on disk.
            explanation_md = ""

        return ExplainResult(request=payload, response=resp, explanation_md=explanation_md)

    # ---------------------------
    # Helpers
    # ---------------------------

    @staticmethod
    def _raise_for_status(r: requests.Response, context: str) -> None:
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            body = r.text[:4000]
            raise CEError(f"{context} failed: HTTP {r.status_code}\n{body}") from e


def _json_dump(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _text_dump(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _split_flags(user_arguments: str) -> List[str]:
    """
    Conservative split: CE explain API expects an array of strings (e.g., ["-O2","-std=c++20"]). :contentReference[oaicite:12]{index=12}
    This is not a full shell parser; if you need quotes, pass compilation_options yourself.
    """
    return [x for x in user_arguments.strip().split() if x]


def _stable_hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="replace")).hexdigest()[:16]


def process_source_tree(
    *,
    src_root: Path,
    out_root: Path,
    client: CompilerExplorerClient,
    compiler_id: str,
    scenario_name: str = "",
    ce_lang_id: Optional[str] = None,
    ce_user_arguments: str = "-O2",
    explain_language: str = "c++",
    explain_compiler_human: str = "unknown",
    instruction_set: str = "amd64",
    explain_audience: str = "beginner",
    explain_type: str = "assembly",
    bypass_compile_cache: int = 0,
    bypass_explain_cache: bool = False,
    extensions: Tuple[str, ...] = (".c", ".cc", ".cpp", ".cxx", ".C", ".h", ".hpp"),
    sleep_s: float = 0.0,
    progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
    file_index_offset: int = 0,
    total_files_global: int = 0,
) -> int:
    """
    Walks src_root recursively, processes each matching file, and writes outputs under out_root
    preserving directory structure.

    Input layout example:
      src/loops/unrollme-1.c

    Output layout example:
      out/loops/unrollme-1.src.c
      out/loops/unrollme-1.compile.request.json
      out/loops/unrollme-1.compile.response.json
      out/loops/unrollme-1.asm
      out/loops/unrollme-1.explain.request.json
      out/loops/unrollme-1.explain.response.json
      out/loops/unrollme-1.explain.md

    Returns the number of files processed.
    """
    src_root = src_root.resolve()
    out_root = out_root.resolve()
    if not src_root.exists() or not src_root.is_dir():
        raise CEError(f"src_root does not exist or is not a directory: {src_root}")

    files = sorted([p for p in src_root.rglob("*") if p.is_file() and p.suffix in extensions])
    total = total_files_global if total_files_global > 0 else len(files)

    for i, p in enumerate(files):
        rel_dir = p.parent.relative_to(src_root)
        out_dir = out_root / rel_dir
        base = p.stem  # "unrollme-1" from "unrollme-1.c"
        rel_path = str(rel_dir / base) if str(rel_dir) != "." else base
        src_text = p.read_text(encoding="utf-8", errors="replace")

        # Parse per-file gallery hints and apply compiler/scenario filters.
        hints = parse_gallery_hints(src_text)
        if not hints.should_compile(compiler_id, scenario_name):
            continue
        effective_flags = hints.effective_flags(ce_user_arguments)

        current_index = file_index_offset + i + 1

        # Always write a copy of the input source for traceability.
        _text_dump(out_dir / f"{base}.src{p.suffix}", src_text)

        # Progress: compile
        if progress_callback:
            progress_callback(ProgressInfo(
                compiler_id=compiler_id,
                scenario=scenario_name,
                source_file=rel_path,
                step="compile",
                current=current_index,
                total=total,
            ))

        # Compile
        comp = client.compile_to_asm(
            compiler_id=compiler_id,
            source=src_text,
            user_arguments=effective_flags,
            lang=ce_lang_id,
            bypass_cache=bypass_compile_cache,
        )
        _json_dump(out_dir / f"{base}.compile.request.json", comp.request)
        _json_dump(out_dir / f"{base}.compile.response.json", comp.response)
        _text_dump(out_dir / f"{base}.asm", comp.asm_text)

        # Progress: explain
        if progress_callback:
            progress_callback(ProgressInfo(
                compiler_id=compiler_id,
                scenario=scenario_name,
                source_file=rel_path,
                step="explain",
                current=current_index,
                total=total,
            ))

        # Explain (feed asm lines as array of dicts with "text" key)
        asm_lines = [{"text": line} for line in comp.asm_text.splitlines()]

        # Use instruction set from compile response if available (more accurate)
        actual_instruction_set = comp.response.get("instructionSet", instruction_set)

        exp = client.explain_assembly(
            language=explain_language,
            compiler=explain_compiler_human,
            code=src_text,
            compilation_options=_split_flags(effective_flags),
            instruction_set=actual_instruction_set,
            asm_lines=asm_lines,
            audience=explain_audience,
            explanation_type=explain_type,
            bypass_cache=bypass_explain_cache,
        )
        _json_dump(out_dir / f"{base}.explain.request.json", exp.request)
        _json_dump(out_dir / f"{base}.explain.response.json", exp.response)
        _text_dump(out_dir / f"{base}.explain.md", exp.explanation_md)

        if sleep_s > 0:
            time.sleep(sleep_s)

    return len(files)


# ---------------------------
# Example usage (as a script)
# ---------------------------

if __name__ == "__main__":
    # Example: process ./src into ./out preserving subdirs.
    # Pick a compiler ID from GET /api/compilers/<language-id>. :contentReference[oaicite:13]{index=13}
    #
    # For C, a common choice on godbolt is something like "cg173" (varies over time).
    # You should programmatically list compilers and pick the one you want.
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="Path to src directory root (the folder containing loops/, etc.)")
    ap.add_argument("--out", required=True, help="Output directory root")
    ap.add_argument("--compiler-id", required=True, help="Compiler Explorer compiler ID (e.g., g122, clang_trunk, etc.)")
    ap.add_argument("--lang", default=None, help="Optional CE lang id (e.g., 'c', 'c++')")
    ap.add_argument("--flags", default="-O2", help="Compiler flags/userArguments")
    ap.add_argument("--explain-language", default="c", help="Explain API language field (e.g., c, c++)")
    ap.add_argument("--explain-compiler", default="unknown", help="Human compiler name for Explain payload (e.g., GCC 13.2)")
    ap.add_argument("--instruction-set", default="amd64", help="Explain API instructionSet (e.g., amd64)")
    ap.add_argument("--audience", default="beginner", choices=["beginner", "experienced"])
    ap.add_argument("--explain-type", default="assembly", choices=["assembly", "haiku"])
    ap.add_argument("--ce-base-url", default="https://godbolt.org", help="Compiler Explorer base URL")
    ap.add_argument("--explain-base-url", default="https://api.compiler-explorer.com/explain", help="Explain base URL")
    ap.add_argument("--sleep", type=float, default=0.0, help="Sleep between files (seconds)")
    ap.add_argument("--bypass-compile-cache", type=int, default=0, help="0/1/2 bypassCache enum for CE compile")
    ap.add_argument("--bypass-explain-cache", action="store_true", help="Bypass Explain caches")
    args = ap.parse_args()

    client = CompilerExplorerClient(
        ce_base_url=args.ce_base_url,
        explain_base_url=args.explain_base_url,
    )

    process_source_tree(
        src_root=Path(args.src),
        out_root=Path(args.out),
        client=client,
        compiler_id=args.compiler_id,
        ce_lang_id=args.lang,
        ce_user_arguments=args.flags,
        explain_language=args.explain_language,
        explain_compiler_human=args.explain_compiler,
        instruction_set=args.instruction_set,
        explain_audience=args.audience,
        explain_type=args.explain_type,
        bypass_compile_cache=args.bypass_compile_cache,
        bypass_explain_cache=args.bypass_explain_cache,
        sleep_s=args.sleep,
    )
