/*
 * Integer promotion surprises: C promotes small types to int
 * before arithmetic, which can cause unexpected sign extension
 * and change comparison results.
 *
 * Real-world: Common source of bugs in embedded code and
 * protocol parsers where uint8_t/uint16_t are used.
 */
#include <stdint.h>

/* Surprising: 0xFF as uint8_t, promoted to int, then compared.
 * The bitwise NOT of (int)0xFF is (int)0xFFFFFF00, a large
 * positive number (unsigned) or negative (signed).
 */
int promotion_surprise(uint8_t byte)
{
    /* ~byte promotes byte to int first: ~(int)0xFF = (int)0xFFFFFF00
     * This is -256 as signed int, not 0x00 as you might expect.
     * Comparing against an unsigned type yields surprising results.
     */
    if (~byte == 0)     /* never true! ~0xFF == -256, not 0 */
        return 1;
    return 0;
}

/* Explicit masking after promotion */
int promotion_safe(uint8_t byte)
{
    if ((uint8_t)(~byte) == 0)  /* (uint8_t)(~0xFF) == 0x00 -- correct */
        return 1;
    return 0;
}

/* Sign extension during widening: uint16_t → int → uint32_t */
uint32_t widen_bad(uint16_t port, uint16_t flags)
{
    /* flags is promoted to signed int before shift.
     * If flags has bit 15 set (e.g. 0x8000), the shift result
     * is negative, and widening to uint32_t sign-extends to
     * 0xFFFF80000000 -- not what was intended.
     */
    return ((uint32_t)port << 16) | (flags << 0);
    /* This specific case is fine, but (flags << 16) would be UB
     * because flags promoted to int, shifted left into sign bit.
     */
}
