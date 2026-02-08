/*
 * Security issue: null pointer check eliminated after dereference.
 *
 * Compiler assumes dereferencing null is UB, so if you dereference
 * first, any subsequent null check is "impossible" and removed.
 */
#include <stddef.h>

struct data {
    int value;
    int flags;
};

int process(struct data *p)
{
    int val;

    /* Dereference first */
    val = p->value;

    /* Check for null afterward - THIS MAY BE REMOVED!
     * Compiler reasons: "p was dereferenced, so p cannot be null,
     * therefore this check is always false"
     */
    if (p == NULL)
        return -1;

    return val + p->flags;
}
