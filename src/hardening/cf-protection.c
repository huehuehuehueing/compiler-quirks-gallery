/* @gallery-hints
 *   extra-flags: -fcf-protection=full
 *   compiler-only: cg152, clang1910
 */

/*
 * Control-Flow Enforcement (CET / IBT + Shadow Stack)
 *
 * -fcf-protection=full enables Intel CET instrumentation:
 *   - IBT (Indirect Branch Tracking): indirect calls/jumps must land
 *     on an ENDBR64 instruction, otherwise a #CP fault occurs.
 *   - Shadow Stack: CALL pushes return addresses to a hardware shadow
 *     stack; RET checks both stacks match, preventing ROP attacks.
 *
 * Look for: ENDBR64 at function entry points and at indirect branch
 * targets.
 */

typedef int (*op_fn)(int, int);

int add(int a, int b) { return a + b; }
int sub(int a, int b) { return a - b; }

int apply(op_fn f, int x, int y)
{
    return f(x, y);
}

int demo(void)
{
    return apply(add, 10, 3) + apply(sub, 10, 3);
}
