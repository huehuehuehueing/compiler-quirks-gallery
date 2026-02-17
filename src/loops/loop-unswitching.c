/*
 * Loop unswitching: moving a loop-invariant conditional outside
 * the loop by creating two copies of the loop body.
 *
 * The optimizer duplicates the loop -- one copy for the true
 * branch, one for the false branch -- so the branch is only
 * evaluated once instead of N times.
 *
 * Trade-off: doubles code size for the loop body.
 * At -Os this optimization is typically suppressed.
 */

extern void process_a(int val);
extern void process_b(int val);

/* The if(flag) is invariant across all iterations.
 * At -O2/-O3 the compiler creates two loop copies:
 *   if (flag) { for(...) process_a(data[i]); }
 *   else      { for(...) process_b(data[i]); }
 */
void process_array(const int *data, int n, int flag)
{
    for (int i = 0; i < n; i++) {
        if (flag) {
            process_a(data[i]);
        } else {
            process_b(data[i]);
        }
    }
}
