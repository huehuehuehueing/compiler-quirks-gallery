/*
 * Loop-Invariant Code Motion (LICM)
 *
 * The optimizer recognises computations inside a loop whose result
 * does not change across iterations and moves ("hoists") them before
 * the loop.  This avoids redundant work on every iteration.
 *
 * In the example below, `base * scale` is invariant with respect to
 * the loop index i, so the compiler should compute it once and reuse
 * the result inside the loop body.
 */

void fill_scaled(int *arr, int n, int base, int scale)
{
    for (int i = 0; i < n; i++)
    {
        /* base * scale is loop-invariant: it does not depend on i. */
        arr[i] = base * scale + i;
    }
}
