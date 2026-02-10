/*
 * Loop Interchange
 *
 * When iterating over a 2D array, the order of the loop indices
 * determines memory access patterns.  In C (row-major layout),
 * iterating the inner loop over columns and the outer loop over
 * rows yields sequential access.  Swapping the loops ("interchange")
 * can improve cache locality when the original order would cause
 * stride-N accesses.
 *
 * Here the "bad" order (column-major traversal on a row-major array)
 * is presented; the compiler may interchange the loops at -O3.
 */
#define N 128

void column_sum(int mat[N][N], int result[N])
{
    /* Column-major traversal: inner loop strides by N ints.
     * The compiler may swap i and j for better locality. */
    for (int j = 0; j < N; j++)
    {
        result[j] = 0;
        for (int i = 0; i < N; i++)
        {
            result[j] += mat[i][j];
        }
    }
}
