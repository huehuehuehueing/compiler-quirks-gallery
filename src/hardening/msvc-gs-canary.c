/* @gallery-hints
 *   replace-flags: /O2 /GS
 *   compiler-only: vc_v19_44_VS17_14_x64, vc_v19_44_VS17_14_x86
 */

/*
 * MSVC Buffer Security Check (/GS)
 *
 * /GS is MSVC's stack canary, analogous to GCC's -fstack-protector.
 * The compiler places a copy of __security_cookie (XORed with RSP)
 * between local buffers and the saved return address.  Before the
 * function returns it calls __security_check_cookie; if the canary
 * was corrupted the process terminates.
 *
 * Compare with stack-protector.c (GCC/Clang):
 *   - GCC reads the canary from a thread-local slot (%fs:0x28).
 *   - MSVC reads a global __security_cookie and XORs it with RSP,
 *     making each frame's canary value unique.
 *
 * Look for: mov rax, __security_cookie / xor rax, rsp at the
 * prologue, and __security_check_cookie before the epilogue.
 */
#include <string.h>

void copy_input(const char *input)
{
    char buf[64];
    strcpy(buf, input);   /* intentionally unsafe for demonstration */
    (void)buf;
}
