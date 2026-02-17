/*
 * Signed/unsigned comparison in bounds checking.
 *
 * When a signed integer is compared against an unsigned one, the
 * signed value is implicitly converted to unsigned.  A negative
 * signed value becomes a very large unsigned value, bypassing
 * the bounds check entirely.
 *
 * The compiler may also eliminate the negative-value branch when
 * it can prove the comparison always succeeds after promotion.
 *
 * Real-world: CVE-2018-8781 (Linux udl driver), CVE-2014-1266
 * (Apple SSL), countless off-by-one / missed-bounds-check bugs.
 */
#include <stddef.h>
#include <string.h>

extern void process(const void *buf, size_t len);

/* BUG: signed 'offset' compared against unsigned 'bufsize'.
 * If offset is negative, (size_t)offset wraps to a huge value,
 * PASSING the check and causing an out-of-bounds read.
 *
 * At -O2 the compiler may remove the upper-bound check entirely
 * if it deduces that the promoted value is always < bufsize.
 */
void read_at_bad(const char *buf, size_t bufsize, int offset, size_t len)
{
    if (offset + len <= bufsize) {        /* signed + unsigned → unsigned */
        process(buf + offset, len);       /* offset can be negative */
    }
}

/* BUG: loop with signed index vs unsigned bound.
 * If 'count' comes from untrusted input and is negative,
 * the loop condition (int < unsigned) promotes count's sign bit:
 *   -1 → 0xFFFFFFFF as unsigned → loops ~4 billion times.
 */
void fill_bad(char *buf, size_t bufsize, int count, char val)
{
    if ((size_t)count > bufsize)   /* cast "fixes" negativity check... */
        return;                    /* ...but -1 → SIZE_MAX, still passes! */

    for (int i = 0; i < count; i++) {
        buf[i] = val;
    }
}

/* SAFE: validate signedness BEFORE any unsigned comparison */
void read_at_safe(const char *buf, size_t bufsize, int offset, size_t len)
{
    if (offset < 0)
        return;

    /* Now offset is non-negative; safe to use as size_t */
    size_t uoffset = (size_t)offset;
    if (uoffset + len <= bufsize) {
        process(buf + uoffset, len);
    }
}

/* SAFE: use matching types for loop bounds */
void fill_safe(char *buf, size_t bufsize, int count, char val)
{
    if (count < 0 || (size_t)count > bufsize)
        return;

    size_t ucount = (size_t)count;
    for (size_t i = 0; i < ucount; i++) {
        buf[i] = val;
    }
}
