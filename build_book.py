#!/usr/bin/env python3
# Copyright (c) 2026 Larry H <l.gr [at] dartmouth [dot] edu>
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Compiler Optimization Gallery
# Developed for COSC-69.16: Basics of Reverse Engineering
# Dartmouth College, Winter 2026

"""
build_book.py

Collects generated explain.md, assembly, and source files from ce_batch.py output
and generates MkDocs-compatible documentation.

Structure: Scenario -> Compiler -> Source

Usage:
    python build_book.py --input output/ --output book/ --config docs/config.yaml

The script uses Jinja2 templates from ./templates/ directory.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import json
import shutil

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError as e:
    raise SystemExit("Missing dependency: jinja2. Install with: pip install jinja2") from e

try:
    import yaml
except ImportError as e:
    raise SystemExit("Missing dependency: pyyaml. Install with: pip install pyyaml") from e


# -----------------------------------------------------------------------------
# Data classes
# -----------------------------------------------------------------------------

@dataclass
class ScenarioConfig:
    """Configuration for a scenario from YAML."""
    name: str
    flags: str
    title: str
    description: str


@dataclass
class CompilerInfo:
    """Information about a compiler."""
    id: str
    scenarios: Set[str] = field(default_factory=set)


@dataclass
class SourceOutput:
    """Output data for a single source/compiler/scenario combination."""
    compiler_id: str
    scenario: str
    source_code: str
    assembly: str
    explanation: str
    source_lang: str


@dataclass
class SourceFile:
    """Represents a source file with all its compiler/scenario outputs."""
    rel_path: str  # e.g., "loops/unrollme-1"
    category: str  # e.g., "loops"
    name: str      # e.g., "unrollme-1"
    extension: str # e.g., ".c"
    outputs: List[SourceOutput] = field(default_factory=list)


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def title_case(text: str) -> str:
    """Convert slug-style text to title case: 'string-literals' -> 'String Literals'."""
    return ' '.join(word.capitalize() for word in text.replace('-', ' ').replace('_', ' ').split())


def detect_language(extension: str) -> str:
    """Map file extension to syntax highlighting language."""
    mapping = {
        ".c": "c",
        ".h": "c",
        ".cc": "cpp",
        ".cpp": "cpp",
        ".cxx": "cpp",
        ".hpp": "cpp",
        ".C": "cpp",
    }
    return mapping.get(extension, "c")


def detect_arch(compiler_id: str) -> str:
    """Detect architecture from compiler ID (Jinja2 filter)."""
    cid = compiler_id.lower()
    if "avr" in cid:
        return "AVR"
    if "arm" in cid or "aarch" in cid:
        return "ARM"
    if "mips" in cid:
        return "MIPS"
    if "sparc64" in cid:
        return "SPARC64"
    if "sparc" in cid:
        return "SPARC"
    if "mingw" in cid or "vc_" in cid or "msvc" in cid:
        return "x86/x64 (Windows)"
    if "clang" in cid or "gcc" in cid or cid.startswith("g") or cid.startswith("c"):
        return "x86/x64"
    return "Unknown"


def normalize_heading_levels(markdown_text: str, min_level: int = 3) -> str:
    """
    Normalize heading levels in markdown text.

    Shifts all headings so the highest level heading becomes min_level.
    This ensures explanations don't have headings that compete with
    the page structure.

    Args:
        markdown_text: The markdown text to process
        min_level: The minimum heading level (default 3 for ###)

    Returns:
        Markdown text with normalized heading levels
    """
    import re

    lines = markdown_text.split('\n')
    result = []

    # First pass: find the minimum heading level in the text
    current_min = 6
    for line in lines:
        match = re.match(r'^(#{1,6})\s', line)
        if match:
            level = len(match.group(1))
            current_min = min(current_min, level)

    # Calculate the shift needed
    if current_min < min_level and current_min <= 6:
        shift = min_level - current_min
    else:
        shift = 0

    # Second pass: apply the shift
    for line in lines:
        match = re.match(r'^(#{1,6})(\s.*)', line)
        if match:
            old_level = len(match.group(1))
            new_level = min(old_level + shift, 6)  # Cap at h6
            result.append('#' * new_level + match.group(2))
        else:
            result.append(line)

    return '\n'.join(result)


def describe_flags(flags: str) -> str:
    """Provide brief description of compiler flags (Jinja2 filter)."""
    if not flags:
        return "Default settings"

    descriptions = []
    if "-O0" in flags:
        descriptions.append("No optimization")
    elif "-O1" in flags:
        descriptions.append("Basic optimization")
    elif "-O3" in flags:
        descriptions.append("Aggressive optimization")
    elif "-O2" in flags:
        descriptions.append("Standard optimization")
    elif "-Os" in flags:
        descriptions.append("Size optimization")
    elif "-Ofast" in flags:
        descriptions.append("Maximum speed optimization")

    if "-g" in flags:
        descriptions.append("debug info")
    if "-march" in flags:
        descriptions.append("architecture-specific")
    if "-flto" in flags:
        descriptions.append("link-time optimization")

    return ", ".join(descriptions) if descriptions else "Custom flags"


# Default scenario descriptions (fallback if not in config)
DEFAULT_SCENARIO_DESCRIPTIONS = {
    "O0": "No optimization. Code is compiled for debugging with no transformations applied.",
    "O1": "Basic optimization level. Enables simple optimizations with minimal compilation time impact.",
    "O2": "Standard optimization level. Good balance between compilation time and runtime performance.",
    "O3": "Aggressive optimization. Enables all O2 optimizations plus loop unrolling, inlining, and vectorization.",
    "Os": "Size optimization. Optimizes for smaller code size rather than speed.",
    "Ofast": "Maximum speed optimization. Enables O3 plus fast-math and other aggressive options.",
}


# -----------------------------------------------------------------------------
# Config loading
# -----------------------------------------------------------------------------

def load_config(config_path: Optional[Path]) -> tuple[Dict[str, ScenarioConfig], Dict[str, str]]:
    """
    Load configuration from YAML file.

    Returns:
        - Dict of scenario configs keyed by scenario name
        - Dict of section display names keyed by directory name
    """
    scenarios: Dict[str, ScenarioConfig] = {}
    sections: Dict[str, str] = {}

    if config_path and config_path.exists():
        obj = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if isinstance(obj, dict):
            # Load scenarios
            scenarios_raw = obj.get("scenarios", {})
            if isinstance(scenarios_raw, dict):
                for name, spec in scenarios_raw.items():
                    if isinstance(spec, dict):
                        flags = spec.get("flags", "")
                        title = spec.get("title", name)
                        desc = spec.get("description", DEFAULT_SCENARIO_DESCRIPTIONS.get(name, f"Optimization level {name}"))
                        scenarios[name] = ScenarioConfig(
                            name=name,
                            flags=flags,
                            title=title,
                            description=desc.strip(),
                        )

            # Load section display names
            sections_raw = obj.get("sections", {})
            if isinstance(sections_raw, dict):
                for key, display_name in sections_raw.items():
                    if isinstance(display_name, str):
                        sections[key] = display_name

    return scenarios, sections


# -----------------------------------------------------------------------------
# Output collection
# -----------------------------------------------------------------------------

def collect_outputs(input_root: Path) -> tuple[Dict[str, SourceFile], Dict[str, CompilerInfo], Set[str]]:
    """
    Walk the input directory and collect all outputs.

    Returns:
        - Dict of source files keyed by relative path
        - Dict of compilers keyed by compiler ID
        - Set of scenario names found
    """
    sources: Dict[str, SourceFile] = {}
    compilers: Dict[str, CompilerInfo] = {}
    scenarios_found: Set[str] = set()

    if not input_root.exists():
        raise SystemExit(f"Input directory does not exist: {input_root}")

    # Structure: input_root/<compiler>/<scenario>/<rel_path>/<stem>.*
    for compiler_dir in sorted(input_root.iterdir()):
        if not compiler_dir.is_dir() or compiler_dir.name.startswith("."):
            continue

        compiler_id = compiler_dir.name
        if compiler_id not in compilers:
            compilers[compiler_id] = CompilerInfo(id=compiler_id)

        for scenario_dir in sorted(compiler_dir.iterdir()):
            if not scenario_dir.is_dir():
                continue

            scenario_name = scenario_dir.name
            scenarios_found.add(scenario_name)
            compilers[compiler_id].scenarios.add(scenario_name)

            # Find all .explain.md files recursively
            for explain_file in scenario_dir.rglob("*.explain.md"):
                stem = explain_file.name.replace(".explain.md", "")
                parent_rel = explain_file.parent.relative_to(scenario_dir)

                # Build the source key
                if str(parent_rel) == ".":
                    source_key = stem
                    category = "general"
                else:
                    source_key = str(parent_rel / stem)
                    category = str(parent_rel).split("/")[0]

                # Find corresponding files
                base_dir = explain_file.parent

                # Find the source file
                source_code = ""
                source_ext = ".c"
                for ext in [".c", ".cc", ".cpp", ".cxx", ".C", ".h", ".hpp"]:
                    src_file = base_dir / f"{stem}.src{ext}"
                    if src_file.exists():
                        source_code = src_file.read_text(encoding="utf-8", errors="replace")
                        source_ext = ext
                        break

                # Read assembly
                asm_file = base_dir / f"{stem}.asm"
                assembly = asm_file.read_text(encoding="utf-8", errors="replace") if asm_file.exists() else ""

                # Read explanation
                explanation = explain_file.read_text(encoding="utf-8", errors="replace")

                # Create or update SourceFile
                if source_key not in sources:
                    sources[source_key] = SourceFile(
                        rel_path=source_key,
                        category=category,
                        name=stem,
                        extension=source_ext,
                    )

                sources[source_key].outputs.append(SourceOutput(
                    compiler_id=compiler_id,
                    scenario=scenario_name,
                    source_code=source_code,
                    assembly=assembly,
                    explanation=explanation,
                    source_lang=detect_language(source_ext),
                ))

    return sources, compilers, scenarios_found


# -----------------------------------------------------------------------------
# Template management
# -----------------------------------------------------------------------------

def ensure_templates(templates_dir: Path) -> None:
    """Create default templates if they don't exist."""
    templates_dir.mkdir(parents=True, exist_ok=True)

    # Main index template
    index_template = templates_dir / "index.md.j2"
    if not index_template.exists():
        index_template.write_text("""\
# {{ title }}

{{ description }}

## Scenarios

{% for scenario in scenarios %}
- [{{ scenario.title }}]({{ scenario.name }}/index.md) - {{ scenario.flags }}
{% endfor %}

## Compilers

See the [compiler reference](compilers.md) for details on all {{ compilers | length }} compilers.

## About

This documentation is auto-generated from Compiler Explorer outputs with AI-powered explanations.
""", encoding="utf-8")

    # Compilers list template
    compilers_template = templates_dir / "compilers.md.j2"
    if not compilers_template.exists():
        compilers_template.write_text("""\
# Compilers

| Compiler ID | Architecture | Scenarios |
|-------------|--------------|-----------|
{% for compiler in compilers %}
| `{{ compiler.id }}` | {{ compiler.id | detect_arch }} | {{ compiler.scenarios | sort | join(", ") }} |
{% endfor %}
""", encoding="utf-8")

    # Scenario index template
    scenario_index_template = templates_dir / "scenario_index.md.j2"
    if not scenario_index_template.exists():
        scenario_index_template.write_text("""\
# {{ scenario.title }}

**Flags:** `{{ scenario.flags }}`

{{ scenario.description }}

## Compilers

{% for compiler in compilers %}
- [{{ compiler.id }}]({{ compiler.id }}/index.md) ({{ compiler.id | detect_arch }})
{% endfor %}
""", encoding="utf-8")

    # Compiler index template (within scenario)
    compiler_index_template = templates_dir / "compiler_index.md.j2"
    if not compiler_index_template.exists():
        compiler_index_template.write_text("""\
# {{ compiler.id }} — {{ scenario.title }}

**Architecture:** {{ compiler.id | detect_arch }}
**Flags:** `{{ scenario.flags }}`

## {{ sources_section }}

{% for section_key, section_data in sections.items() %}
### {{ section_data.title }}

{% for source in section_data.sources %}
- [{{ source.name }}]({{ source.category }}/{{ source.name }}.md)
{% endfor %}

{% endfor %}
""", encoding="utf-8")

    # Source page template
    source_template = templates_dir / "source_page.md.j2"
    if not source_template.exists():
        source_template.write_text("""\
# {{ source.name }}

!!! info "Source File"
    **Path:** `{{ source.rel_path }}{{ source.extension }}`
    **Language:** {{ source_lang | upper }}
    **Compiler:** {{ compiler.id }} ({{ compiler.id | detect_arch }})
    **Scenario:** {{ scenario.title }} (`{{ scenario.flags }}`)

## Source Code

```{{ source_lang }} title="{{ source.name }}{{ source.extension }}"
{{ source_code }}
```

## Assembly Output

```asm title="{{ source.name }}.asm" linenums="1"
{{ assembly }}
```

## Explanation

{{ explanation }}
""", encoding="utf-8")


# -----------------------------------------------------------------------------
# MkDocs config generation
# -----------------------------------------------------------------------------

def generate_mkdocs_config(
    output_dir: Path,
    title: str,
    scenarios: List[ScenarioConfig],
    compilers: List[CompilerInfo],
    sources: Dict[str, SourceFile],
    section_names: Dict[str, str],
) -> None:
    """Generate mkdocs.yml configuration file."""

    # Build a simplified navigation structure
    # Top level: Home, Compilers, then each Scenario
    # Scenario level: index + each compiler (no deeper nesting in nav)
    # Individual pages are linked from index pages, not the nav

    nav: List[Any] = [
        {"Home": "index.md"},
        {"Compilers": "compilers.md"},
    ]

    for scenario in scenarios:
        # Each scenario just lists its compilers, no deeper expansion
        scenario_compilers = [c for c in compilers if scenario.name in c.scenarios]
        scenario_nav: List[Any] = [
            {"Overview": f"{scenario.name}/index.md"},
        ]
        for compiler in sorted(scenario_compilers, key=lambda c: c.id):
            # Just link to compiler index, don't expand categories/sources
            scenario_nav.append({
                compiler.id: f"{scenario.name}/{compiler.id}/index.md"
            })

        nav.append({scenario.title: scenario_nav})

    config = {
        "site_name": title,
        "theme": {
            "name": "material",
            "features": [
                "content.code.copy",
                "navigation.sections",
                "navigation.indexes",
                "navigation.top",
                "toc.follow",
            ],
            "palette": [
                {
                    "scheme": "default",
                    "toggle": {
                        "icon": "material/brightness-7",
                        "name": "Switch to dark mode",
                    },
                },
                {
                    "scheme": "slate",
                    "toggle": {
                        "icon": "material/brightness-4",
                        "name": "Switch to light mode",
                    },
                },
            ],
            "favicon": "assets/favicon.ico",
            "logo": "assets/logo.png",
        },
        "markdown_extensions": [
            "pymdownx.highlight",
            "pymdownx.superfences",
            "pymdownx.inlinehilite",
            "pymdownx.snippets",
            "tables",
            "admonition",
            {"pymdownx.details": None},
            {"toc": {"permalink": True, "toc_depth": 4}},
        ],
        "extra_css": ["custom.css"],
        "nav": nav,
    }

    config_path = output_dir / "mkdocs.yml"
    config_path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False), encoding="utf-8")

    # Generate custom CSS with Dartmouth colors
    docs_dir = output_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "custom.css").write_text("""\
/* Dartmouth Green (#00693e) for header backgrounds with white text */
:root,
[data-md-color-scheme="default"] {
  --md-primary-fg-color: #00693e;
  --md-primary-fg-color--light: #1a7a52;
  --md-primary-fg-color--dark: #004d2e;
  --md-primary-bg-color: #ffffff;
  --md-primary-bg-color--light: #ffffffb3;
  --md-accent-fg-color: #00693e;
}

/* Rich Forest Green (#0D1E1C) for dark mode backgrounds */
[data-md-color-scheme="slate"] {
  --md-primary-fg-color: #00693e;
  --md-primary-fg-color--light: #1a7a52;
  --md-primary-fg-color--dark: #004d2e;
  --md-primary-bg-color: #ffffff;
  --md-primary-bg-color--light: #ffffffb3;
  --md-accent-fg-color: #00693e;
  --md-default-bg-color: #0D1E1C;
  --md-default-bg-color--light: #132926;
}
""", encoding="utf-8")

    # Copy Dartmouth D-Pine logo assets into book
    assets_src = Path(__file__).resolve().parent / "docs" / "assets"
    assets_dst = docs_dir / "assets"
    if assets_src.exists():
        if assets_dst.exists():
            shutil.rmtree(assets_dst)
        shutil.copytree(assets_src, assets_dst)


# -----------------------------------------------------------------------------
# Main build function
# -----------------------------------------------------------------------------

def build_book(
    input_dir: Path,
    output_dir: Path,
    templates_dir: Path,
    config_path: Optional[Path],
    sources_section: str,
    title: str,
    description: str,
) -> None:
    """Main function to build the MkDocs book."""

    # Load config
    scenario_configs, section_names = load_config(config_path)

    # Ensure templates exist
    ensure_templates(templates_dir)

    # Set up Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["detect_arch"] = detect_arch
    env.filters["describe_flags"] = describe_flags
    env.filters["title_case"] = title_case
    env.filters["normalize_headings"] = normalize_heading_levels

    # Collect all outputs
    print(f"Collecting outputs from {input_dir}...")
    sources, compilers, scenarios_found = collect_outputs(input_dir)

    if not sources:
        raise SystemExit("No source outputs found in input directory")

    print(f"Found {len(sources)} source files, {len(compilers)} compilers, {len(scenarios_found)} scenarios")

    # Build scenario list with configs (use found scenarios, with config data if available)
    scenarios_list: List[ScenarioConfig] = []
    for scenario_name in sorted(scenarios_found):
        if scenario_name in scenario_configs:
            scenarios_list.append(scenario_configs[scenario_name])
        else:
            # Create default config
            scenarios_list.append(ScenarioConfig(
                name=scenario_name,
                flags=f"-{scenario_name}" if scenario_name.startswith("O") else "",
                title=scenario_name,
                description=DEFAULT_SCENARIO_DESCRIPTIONS.get(
                    scenario_name,
                    f"Optimization scenario {scenario_name}"
                ),
            ))

    # Create output directories
    docs_dir = output_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Generate main index
    print("Generating index.md...")
    index_template = env.get_template("index.md.j2")
    index_content = index_template.render(
        title=title,
        description=description,
        scenarios=scenarios_list,
        compilers=list(compilers.values()),
    )
    (docs_dir / "index.md").write_text(index_content, encoding="utf-8")

    # Generate compilers page
    print("Generating compilers.md...")
    compilers_template = env.get_template("compilers.md.j2")
    compilers_list = sorted(compilers.values(), key=lambda c: c.id)
    compilers_content = compilers_template.render(
        compilers=[{"id": c.id, "scenarios": sorted(c.scenarios)} for c in compilers_list],
    )
    (docs_dir / "compilers.md").write_text(compilers_content, encoding="utf-8")

    # Generate scenario/compiler/source pages
    print("Generating source pages...")
    scenario_index_template = env.get_template("scenario_index.md.j2")
    compiler_index_template = env.get_template("compiler_index.md.j2")
    source_template = env.get_template("source_page.md.j2")

    for scenario in scenarios_list:
        scenario_dir = docs_dir / scenario.name
        scenario_dir.mkdir(parents=True, exist_ok=True)

        # Get compilers for this scenario
        scenario_compilers = [c for c in compilers_list if scenario.name in c.scenarios]

        # Scenario index
        scenario_index_content = scenario_index_template.render(
            scenario=scenario,
            compilers=scenario_compilers,
        )
        (scenario_dir / "index.md").write_text(scenario_index_content, encoding="utf-8")

        for compiler in scenario_compilers:
            compiler_dir = scenario_dir / compiler.id
            compiler_dir.mkdir(parents=True, exist_ok=True)

            # Group sources by category for this compiler/scenario
            sections: Dict[str, Dict[str, Any]] = {}
            for source in sources.values():
                output = next(
                    (o for o in source.outputs if o.compiler_id == compiler.id and o.scenario == scenario.name),
                    None
                )
                if output:
                    cat = source.category
                    if cat not in sections:
                        sections[cat] = {
                            "title": section_names.get(cat, title_case(cat)),
                            "sources": [],
                        }
                    sections[cat]["sources"].append(source)

            # Sort sources within each section
            for sec in sections.values():
                sec["sources"].sort(key=lambda s: s.name)

            # Compiler index
            compiler_index_content = compiler_index_template.render(
                scenario=scenario,
                compiler=compiler,
                sections=dict(sorted(sections.items())),
                sources_section=sources_section,
            )
            (compiler_dir / "index.md").write_text(compiler_index_content, encoding="utf-8")

            # Source pages
            for source in sources.values():
                output = next(
                    (o for o in source.outputs if o.compiler_id == compiler.id and o.scenario == scenario.name),
                    None
                )
                if not output:
                    continue

                source_dir = compiler_dir / source.category
                source_dir.mkdir(parents=True, exist_ok=True)

                source_content = source_template.render(
                    source=source,
                    source_code=output.source_code,
                    source_lang=output.source_lang,
                    assembly=output.assembly,
                    explanation=output.explanation,
                    scenario=scenario,
                    compiler=compiler,
                )
                (source_dir / f"{source.name}.md").write_text(source_content, encoding="utf-8")

    # Generate mkdocs.yml
    print("Generating mkdocs.yml...")
    generate_mkdocs_config(output_dir, title, scenarios_list, compilers_list, sources, section_names)

    print(f"\nBook generated successfully at {output_dir}/")
    print(f"To preview: cd {output_dir} && mkdocs serve")
    print(f"To build:   cd {output_dir} && mkdocs build")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build MkDocs book from ce_batch.py output"
    )
    ap.add_argument(
        "--input", "-i",
        required=True,
        help="Input directory (output from ce_batch.py)",
    )
    ap.add_argument(
        "--output", "-o",
        required=True,
        help="Output directory for MkDocs project",
    )
    ap.add_argument(
        "--config", "-c",
        default=None,
        help="Path to config.yaml (for scenario descriptions and section names)",
    )
    ap.add_argument(
        "--templates", "-t",
        default="./templates",
        help="Templates directory (default: ./templates)",
    )
    ap.add_argument(
        "--sources-section",
        default="Sources",
        help="Name for the sources section (default: Sources)",
    )
    ap.add_argument(
        "--title",
        default="Compiler Optimization Gallery",
        help="Book title",
    )
    ap.add_argument(
        "--description",
        default="A collection of compiler optimization examples with assembly output and explanations.",
        help="Book description",
    )

    args = ap.parse_args()

    build_book(
        input_dir=Path(args.input),
        output_dir=Path(args.output),
        templates_dir=Path(args.templates),
        config_path=Path(args.config) if args.config else None,
        sources_section=args.sources_section,
        title=args.title,
        description=args.description,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
