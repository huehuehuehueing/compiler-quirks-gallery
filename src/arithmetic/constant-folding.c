/*
 * Constant folding: expressions evaluated at compile time.
 *
 * When all operands are constants, the result is computed
 * during compilation, not at runtime.
 */

int get_buffer_size(void)
{
    /* Entire expression evaluated at compile time.
     * Just returns the constant 4096.
     */
    return 4 * 1024;
}

int complex_constant(void)
{
    /* Even complex expressions with constants are folded.
     * Result: 42
     */
    return (10 + 20) * 2 - 18;
}

/* String length of literal known at compile time */
#include <string.h>

int get_hello_len(void)
{
    /* strlen("hello") is evaluated at compile time to 5 */
    return strlen("hello");
}

/* sizeof is always compile-time */
int get_array_count(void)
{
    int arr[] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
    return sizeof(arr) / sizeof(arr[0]);
}
