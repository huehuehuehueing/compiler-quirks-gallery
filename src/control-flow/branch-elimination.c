/*
 * Branch elimination: compile-time constant conditions.
 *
 * When a branch condition is known at compile time,
 * the dead branch is eliminated entirely.
 */
#include <limits.h>

/* Debug flag - in release builds, debug code is eliminated */
#define DEBUG 0

void maybe_log(const char *msg)
{
    if (DEBUG) {
        /* This entire block is removed when DEBUG is 0 */
        extern void log_message(const char *);
        log_message(msg);
    }
}

/* Platform-specific code */
int get_pointer_size(void)
{
    if (sizeof(void *) == 8) {
        /* Only this branch exists on 64-bit platforms */
        return 64;
    } else {
        /* Only this branch exists on 32-bit platforms */
        return 32;
    }
}

/* Impossible conditions eliminated */
int check_range(int x)
{
    /* If x is already validated as positive elsewhere,
     * and optimizer knows it, this check may be eliminated.
     */
    if (x < 0)
        return -1;

    /* This is always false for signed int */
    if (x > INT_MAX)
        return -2;

    return x;
}
