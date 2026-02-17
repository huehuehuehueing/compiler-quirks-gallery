/*
 * memcpy with overlapping buffers is undefined behavior.
 *
 * memcpy does not guarantee copy direction: the compiler may
 * inline it as a forward or backward copy, or use SIMD.
 * Overlapping regions require memmove, which handles direction.
 *
 * Real-world: CVE-2015-0235 (GHOST) involved buffer handling
 * where overlap assumptions were violated.
 */
#include <string.h>

/* BUG: overlapping memcpy is UB */
void shift_left_bad(char *buf, int len)
{
    /* Copies buf[1..len-1] to buf[0..len-2]
     * Source and destination overlap by len-1 bytes.
     * At -O2+ the compiler may inline this as a single
     * wide load/store that clobbers the source.
     */
    memcpy(buf, buf + 1, len - 1);
    buf[len - 1] = '\0';
}

/* SAFE: memmove handles overlapping regions */
void shift_left_safe(char *buf, int len)
{
    memmove(buf, buf + 1, len - 1);
    buf[len - 1] = '\0';
}
