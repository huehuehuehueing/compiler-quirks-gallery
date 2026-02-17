/*
 * Integer truncation: assigning a wider type to a narrower one
 * silently drops high bits.  The compiler may optimize based on
 * the narrower type's range, eliminating overflow checks.
 *
 * Real-world: CVE-2009-1385 (e1000 driver integer truncation),
 * CVE-2021-22555 (Netfilter length truncation).
 */
#include <stdint.h>
#include <stddef.h>

extern void safe_copy(void *dst, const void *src, size_t n);

/* BUG: size_t → unsigned short truncation loses high bits.
 * A 65540-byte input becomes 4 after truncation, passing
 * the bounds check but overflowing the buffer.
 */
void copy_data_bad(void *dst, const void *src, size_t len)
{
    unsigned short slen = (unsigned short)len;  /* truncation! */

    if (slen <= 1024) {
        /* Looks safe: slen <= 1024, but original len could be 66564 */
        safe_copy(dst, src, len);  /* copies full len, not slen */
    }
}

/* SAFE: validate on the original type before any conversion */
void copy_data_safe(void *dst, const void *src, size_t len)
{
    if (len <= 1024) {
        safe_copy(dst, src, len);
    }
}
