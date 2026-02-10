/* @gallery-hints
 *   extra-flags: -fstack-clash-protection
 *   compiler-exclude: vc_v19_44_VS17_14_x64, vc_v19_44_VS17_14_x86, avrg1520
 */

/*
 * Stack Clash Protection
 *
 * -fstack-clash-protection inserts probes into large stack
 * allocations so that every page of the stack is touched in order.
 * This prevents "stack clash" attacks where a large allocation
 * jumps the guard page and overlaps the heap.
 *
 * Look for: loop-based or sequential page-sized probes (usually
 * stores to rsp at 4096-byte intervals) when the function has a
 * large local frame.
 */

void large_frame(int n)
{
    volatile char buf[16384];  /* larger than one page */
    /* Touch a few spots so the compiler keeps the buffer. */
    buf[0] = 'A';
    buf[4096] = 'B';
    buf[8192] = 'C';
    buf[16383] = 'D';
    (void)n;
}
