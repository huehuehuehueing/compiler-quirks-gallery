/* @gallery-hints
 *   extra-flags: -fwrapv
 */

/*
 * -fwrapv: well-defined signed integer overflow
 *
 * By default, signed integer overflow is undefined behaviour in C,
 * and compilers exploit this for optimisation (e.g. assuming i+1 > i).
 * With -fwrapv, signed overflow wraps around in two's complement,
 * which is well-defined.
 *
 * Compare the assembly with and without -fwrapv: the optimizer may
 * remove overflow checks or fold comparisons differently when
 * overflow is undefined.
 */

int will_overflow(int x)
{
    /* Without -fwrapv the compiler may assume this never wraps,
     * optimising the comparison to always-true. */
    if (x + 1 > x)
        return 1;
    return 0;
}

int abs_safe(int x)
{
    /* With well-defined wrapping, the compiler must handle INT_MIN. */
    if (x < 0)
        x = -x;
    return x;
}
