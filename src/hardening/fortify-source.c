/* @gallery-hints
 *   extra-flags: -D_FORTIFY_SOURCE=2
 *   compiler-only: cg152, clang1910
 *   scenario-exclude: O0
 */

/*
 * FORTIFY_SOURCE - compile-time and runtime buffer overflow checks.
 *
 * When _FORTIFY_SOURCE is defined (requires optimization >= -O1),
 * glibc replaces common functions like memcpy, strcpy, sprintf with
 * checked variants (__memcpy_chk, etc.) that verify the destination
 * buffer size at compile time or runtime.
 *
 * Look for: calls to __memcpy_chk or __strcpy_chk instead of plain
 * memcpy / strcpy.  If the compiler can prove the copy is safe at
 * compile time, the check is elided entirely.
 */
#include <string.h>

void safe_copy(char *dst, unsigned long dstsize, const char *src)
{
    /* With FORTIFY_SOURCE, this becomes __memcpy_chk which will
     * abort at runtime if srclen > dstsize. */
    size_t srclen = strlen(src) + 1;
    if (srclen <= dstsize)
        memcpy(dst, src, srclen);
}

void known_size_copy(void)
{
    char buf[32];
    /* Compiler knows buf is 32 bytes, so it can check at compile time. */
    strcpy(buf, "hello");
    (void)buf;
}
