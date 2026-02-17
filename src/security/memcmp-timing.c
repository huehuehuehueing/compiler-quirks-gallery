/*
 * Timing side channel: memcmp short-circuits on first mismatch.
 *
 * The compiler may further optimize a byte-by-byte comparison
 * loop into word-sized comparisons that also short-circuit,
 * leaking how many bytes of a secret matched.
 *
 * Real-world: CVE-2014-0160 (Heartbleed context), countless
 * authentication bypass bugs from non-constant-time comparisons.
 */
#include <string.h>
#include <stdint.h>
#include <stddef.h>

/* VULNERABLE: memcmp returns early on first mismatched byte.
 * An attacker measuring response time can determine how many
 * bytes of their guess matched the secret.
 */
int verify_token_bad(const char *input, const char *secret, size_t len)
{
    return memcmp(input, secret, len) == 0;
}

/* SAFE: constant-time comparison -- always examines all bytes.
 * The result is accumulated via OR so no branch depends on data.
 * The volatile prevents the compiler from short-circuiting.
 */
int verify_token_safe(const uint8_t *input, const uint8_t *secret, size_t len)
{
    volatile uint8_t diff = 0;
    for (size_t i = 0; i < len; i++) {
        diff |= input[i] ^ secret[i];
    }
    return diff == 0;
}
