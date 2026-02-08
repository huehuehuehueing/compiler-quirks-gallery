/*
 * memcpy inlining: small copies become inline loads/stores.
 *
 * For small, known-size copies, the compiler generates
 * inline code instead of calling memcpy.
 */
#include <string.h>

struct small {
    int a, b;
};

void copy_8_bytes(void *dst, const void *src)
{
    /* Small copy - likely inlined as single 64-bit load/store
     * on 64-bit architectures, or two 32-bit ops on 32-bit.
     */
    memcpy(dst, src, 8);
}

void copy_struct(struct small *dst, const struct small *src)
{
    /* Structure copy - same as memcpy but type-aware.
     * Compiler knows alignment and size.
     */
    *dst = *src;
}

void copy_varying(void *dst, const void *src, int use_large)
{
    /* Compile-time unknown size - must call memcpy or
     * generate size-checking code.
     */
    if (use_large)
        memcpy(dst, src, 1024);
    else
        memcpy(dst, src, 8);
}
