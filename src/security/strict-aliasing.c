/*
 * Strict aliasing violation: type punning through pointer casts.
 *
 * This code has undefined behavior under strict aliasing rules.
 * Results vary based on -fstrict-aliasing (default in O2+) vs
 * -fno-strict-aliasing.
 */
#include <stdint.h>

/* Convert float bits to int (WRONG WAY - UB with strict aliasing) */
uint32_t float_bits_bad(float f)
{
    /* Violates strict aliasing - float and uint32_t are
     * not compatible types, so compiler may assume they
     * don't alias and optimize incorrectly.
     */
    return *(uint32_t *)&f;
}

/* The safe way using union (well-defined in C99+) */
uint32_t float_bits_safe(float f)
{
    union {
        float f;
        uint32_t u;
    } conv;
    conv.f = f;
    return conv.u;
}
