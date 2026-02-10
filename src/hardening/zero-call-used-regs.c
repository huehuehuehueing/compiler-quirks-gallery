/* @gallery-hints
 *   extra-flags: -fzero-call-used-regs=used
 *   compiler-only: cg152, clang1910
 */

/*
 * Zero Call-Used Registers
 *
 * -fzero-call-used-regs=used clears every register that the function
 * actually used before returning. This mitigates information leakage
 * through registers and makes ROP gadgets less useful because
 * attackers cannot rely on register contents at a ret instruction.
 *
 * Look for: xor or zero instructions on registers (eax, ecx, edx,
 * xmm0, etc.) immediately before the ret instruction.
 */

int compute(int a, int b, int c)
{
    int result = a * b + c;
    return result;
}

long long widen(int x)
{
    return (long long)x * x;
}
