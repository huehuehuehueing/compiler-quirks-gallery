/*
 * Return value used after free / scope exit.
 *
 * Returning a pointer to a local variable is UB.  The compiler may
 * warn but still generates code that "works" at -O0 because the
 * stack frame hasn't been overwritten yet.  At -O2+ the local may
 * be optimized into a register and the returned pointer is garbage.
 *
 * Real-world: CVE-2017-6074 (DCCP double-free, related stack reuse).
 */
#include <stddef.h>

struct token {
    int type;
    int value;
};

/* BUG: returns address of stack local */
struct token *parse_next_bad(const char *input)
{
    struct token t;
    t.type = input[0];
    t.value = input[1] | (input[2] << 8);
    return &t;  /* dangling pointer */
}

/* SAFE: caller provides storage */
struct token *parse_next_safe(const char *input, struct token *out)
{
    out->type = input[0];
    out->value = input[1] | (input[2] << 8);
    return out;
}
