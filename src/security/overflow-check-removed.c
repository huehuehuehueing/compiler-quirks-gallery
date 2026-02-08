/*
 * Security issue: integer overflow check removed.
 *
 * Signed integer overflow is undefined behavior in C.
 * Compiler may assume it never happens and remove checks.
 */
#include <limits.h>

int safe_add(int a, int b)
{
    /* Attempt to check for overflow before it happens.
     * With optimization, this check may be REMOVED because
     * the compiler assumes signed overflow is impossible.
     */
    if (a > 0 && b > 0 && a > INT_MAX - b)
        return -1;  /* overflow would occur */

    if (a < 0 && b < 0 && a < INT_MIN - b)
        return -1;  /* underflow would occur */

    return a + b;
}
