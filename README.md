# Compiler Optimization Gallery

A curated collection of C source code examples demonstrating compiler optimization behaviors, quirks, and security implications across multiple architectures and optimization levels.

This project was developed for **Prof. Sergey Bratus' Basics of Reverse Engineering course (COSC-69.16)** at Dartmouth College during the Winter 2026 term.

It uses [Compiler Explorer (Godbolt)](https://godbolt.org) to generate assembly output and AI-powered explanations, then packages everything into a browsable [MkDocs](https://www.mkdocs.org/) documentation site.

## Features

- **Cross-architecture comparison**: See how the same code compiles on x86, ARM, AVR, MIPS, SPARC, and more
- **Multiple optimization levels**: Compare `-O0`, `-O2`, `-O3`, `-Os`, and `-Ofast` side by side
- **AI-powered explanations**: Each assembly output includes a detailed explanation of what the compiler did and why
- **Security-focused examples**: Demonstrates dangerous optimizations that can introduce vulnerabilities
- **Jinja2 templates**: Fully customizable output format
- **Progress tracking**: Real-time ETA and progress display during batch processing

## Example Categories

| Category | Description |
|----------|-------------|
| **Security** | Optimizations with security implications (memset removal, null check elimination, overflow check removal) |
| **Arithmetic** | Strength reduction, constant folding, fast-math effects |
| **Memory** | memcpy inlining, stack reuse, volatile semantics |
| **Control Flow** | Tail call optimization, branch elimination, function inlining, switch tables |
| **SIMD** | Auto-vectorization, restrict pointer effects |
| **Loops** | Dead code elimination, loop unrolling |
| **String Literals** | Static initialization, string copying patterns |

## Quick Start

```bash
# Install dependencies
make install

# Run the full pipeline (compile + generate book)
make all

# Preview the documentation locally
make serve
```

Then open http://127.0.0.1:8000 in your browser.

## Requirements

- Python 3.8+
- Internet connection (for Compiler Explorer API)

Python dependencies (installed via `make install`):
- `requests` - HTTP client for Compiler Explorer API
- `pyyaml` - YAML configuration parsing
- `jinja2` - Template rendering
- `mkdocs-material` - Documentation theme

## Usage

### Make Targets

```
make help        # Show all targets and configuration
make install     # Install Python dependencies
make compile     # Run Compiler Explorer batch processing
make book        # Generate MkDocs documentation
make serve       # Serve MkDocs locally at http://127.0.0.1:8000
make build       # Build static HTML site
make all         # Full pipeline: compile + book (default)
make clean       # Remove compiler output
make clean-all   # Remove output and book directories
make rebuild     # Clean everything and rebuild from scratch
```

### Configuration

Edit `docs/config.yaml` to customize scenarios, compilers, and section names:

```yaml
scenarios:
  O2:
    flags: "-O2"
    title: "O2 - Standard Optimization"
    description: |
      Standard optimization level providing a good balance...

compilers:
  - cg152          # GCC x86-64
  - clang1910      # Clang x86-64
  - armv8-clang2110  # ARM64

sections:
  security: "Security-Critical Optimizations"
  loops: "Loop Optimizations"
```

### Adding New Examples

1. Create a new `.c` file in the appropriate `src/` subdirectory
2. Run `make compile` to generate assembly and explanations
3. Run `make book` to regenerate the documentation

## Sample Output

### Progress Display

```
$ make compile
python3 ce_batch.py --yaml docs/config.yaml --src src --out output
Loading config from docs/config.yaml...
  5 scenarios, 11 compilers
Validating compiler IDs... OK (11 compilers)
Found 23 source files
Total: 1265 file compilations (23 files x 11 compilers x 5 scenarios)

[cg152][O2][security/memset-removed] explain (142/1265)  11.2% | elapsed: 5m 12s | ETA: 41m 8s
```

### Generated Assembly Example

**Source** (`src/security/memset-removed.c`):
```c
void process_password(const char *password)
{
    char local_copy[64];
    strncpy(local_copy, password, sizeof(local_copy) - 1);
    local_copy[sizeof(local_copy) - 1] = '\0';

    /* Security: clear the password from stack
     * BUG: This memset is often REMOVED by optimizer!
     */
    memset(local_copy, 0, sizeof(local_copy));
}
```

**Assembly** (x86-64 GCC -O2):
```asm
process_password:
        sub     rsp, 72
        mov     edx, 63
        lea     rdi, [rsp+8]
        mov     rsi, rdi
        call    strncpy
        mov     BYTE PTR [rsp+71], 0
        add     rsp, 72
        ret
        ; NOTE: memset call is completely absent!
```

**AI Explanation** (excerpt):
> The most critical observation here is what's **missing**: the `memset()` call to clear the password has been completely eliminated by the optimizer.
>
> The compiler determined that `local_copy` is never read after the `memset()`, so the clearing operation has "no effect" on program behavior. This is a textbook example of a security-critical optimization bug...

### Generated Documentation Structure

```
book/
├── mkdocs.yml
└── docs/
    ├── index.md
    ├── compilers.md
    ├── O2/
    │   ├── index.md
    │   ├── cg152/
    │   │   ├── index.md
    │   │   ├── security/
    │   │   │   ├── memset-removed.md
    │   │   │   ├── null-check-removed.md
    │   │   │   └── ...
    │   │   ├── arithmetic/
    │   │   └── ...
    │   └── clang1910/
    │       └── ...
    ├── O3/
    └── ...
```

## Project Structure

```
.
├── Makefile                 # Build automation
├── ce_batch.py              # Batch processing script
├── ce_client.py             # Compiler Explorer API client
├── build_book.py            # MkDocs generator
├── docs/
│   └── config.yaml          # Scenarios, compilers, sections
├── src/                     # Source code examples
│   ├── security/
│   ├── arithmetic/
│   ├── memory/
│   ├── control-flow/
│   ├── simd/
│   ├── loops/
│   └── string-literals/
├── templates/               # Jinja2 templates
│   ├── index.md.j2
│   ├── compilers.md.j2
│   ├── scenario_index.md.j2
│   ├── compiler_index.md.j2
│   └── source_page.md.j2
├── output/                  # Generated assembly (gitignored)
└── book/                    # Generated MkDocs site (gitignored)
```

## Supported Compilers

| Compiler | Architecture | ID |
|----------|--------------|-----|
| GCC | x86-64 | `cg152` |
| Clang | x86-64 | `clang1910` |
| MSVC | x86-64 | `vc_v19_44_VS17_14_x64` |
| MSVC | x86 | `vc_v19_44_VS17_14_x86` |
| MinGW GCC | x86-64 | `cmingw64_ucrt_gcc_1520` |
| GCC | AVR | `avrg1520` |
| GCC | MIPS | `mipsg1520` |
| GCC | SPARC | `csparcg1520` |
| GCC | SPARC64 | `csparc64g1520` |
| Clang | ARMv7 | `armv7-clang2110` |
| Clang | ARMv8/AArch64 | `armv8-clang2110` |

See [Compiler Explorer API](https://godbolt.org/api/compilers) for the full list of available compilers.

## License

GNU Affero General Public License v3.0 (AGPL-3.0)

Copyright (c) 2026 Larry H

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

If you modify this program and make it available over a network, you must
provide the complete corresponding source code to users interacting with it
remotely.

See [LICENSE](LICENSE) for the full license text.

## Contributors and Authors

### Primary Author

- **Larry H** - Dartmouth College (<l.gr [at] dartmouth [dot] edu>)

### Course

- **COSC-69.16: Basics of Reverse Engineering** - Winter 2026
- **Instructor**: Prof. Sergey Bratus, Dartmouth College

### Acknowledgments

- [Compiler Explorer (Godbolt)](https://godbolt.org) - Matt Godbolt and contributors
- [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) - Martin Donath
- Assembly explanations powered by Claude (Anthropic)

---

*This project is intended for educational purposes to help developers understand how compilers optimize code and the potential security implications of certain optimization patterns.*
