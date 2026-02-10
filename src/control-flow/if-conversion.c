/*
 * If-Conversion (branch to conditional move)
 *
 * Short if-else chains that select between two values can be
 * replaced with conditional-move instructions (cmov on x86).
 * This eliminates a branch, avoiding potential misprediction
 * penalties on modern super-scalar CPUs.
 *
 * Look for: cmovl / cmovge / cmovne instead of jl / jge / jne
 * with a branch over a mov.
 */

int min(int a, int b)
{
    if (a < b)
        return a;
    return b;
}

int clamp(int x, int lo, int hi)
{
    if (x < lo)
        x = lo;
    if (x > hi)
        x = hi;
    return x;
}

int abs_val(int x)
{
    return x < 0 ? -x : x;
}
