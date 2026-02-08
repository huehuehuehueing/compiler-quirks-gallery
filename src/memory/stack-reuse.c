/*
 * Stack slot reuse: non-overlapping locals share stack space.
 *
 * The compiler analyzes variable lifetimes and reuses
 * stack slots for variables that are never live at the same time.
 */
#include <stdio.h>

void example(int flag)
{
    if (flag) {
        /* This buffer is only live in this branch */
        char buffer_a[100];
        snprintf(buffer_a, sizeof(buffer_a), "Path A: %d", flag);
        printf("%s\n", buffer_a);
    } else {
        /* This buffer may reuse the same stack slot as buffer_a
         * since they're never both alive at the same time.
         */
        char buffer_b[100];
        snprintf(buffer_b, sizeof(buffer_b), "Path B: %d", flag);
        printf("%s\n", buffer_b);
    }

    /* Total stack usage may be ~100 bytes, not 200 */
}
