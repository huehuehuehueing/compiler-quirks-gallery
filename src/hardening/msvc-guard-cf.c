/* @gallery-hints
 *   replace-flags: /O2 /guard:cf
 *   compiler-only: vc_v19_44_VS17_14_x64, vc_v19_44_VS17_14_x86
 */

/*
 * MSVC Control Flow Guard (/guard:cf)
 *
 * Control Flow Guard (CFG) is a Windows platform security feature
 * that validates every indirect call at runtime.  The compiler
 * replaces indirect CALL instructions with a dispatch through
 * __guard_dispatch_icall_fptr, which checks the target address
 * against a bitmap of valid call targets before transferring
 * control.
 *
 * Compare with cf-protection.c (GCC/Clang):
 *   - GCC/Clang use Intel CET hardware: ENDBR64 marks valid
 *     landing pads, and the CPU faults on violations.
 *   - MSVC CFG is a software bitmap check performed in user-mode
 *     before every indirect call; it works on all x86/x64 CPUs.
 *
 * Look for: rex_jmp __guard_dispatch_icall_fptr (or
 * __guard_check_icall_fptr) where a plain indirect call would
 * normally appear.
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
