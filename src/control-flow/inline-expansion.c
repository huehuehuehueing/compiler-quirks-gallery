/*
 * Function inlining: small functions are expanded at call site.
 *
 * Eliminates call overhead and enables further optimizations
 * by exposing the function body to the caller's context.
 */

/* Tiny function - almost certainly inlined */
static inline int square(int x)
{
    return x * x;
}

/* Using static helps inlining (internal linkage) */
static int cube(int x)
{
    return x * x * x;
}

/* Wrapper that uses inlined functions */
int compute(int x)
{
    /* After inlining, this becomes:
     * return (x * x) + (x * x * x);
     * Which may further simplify to:
     * return x * x * (1 + x);
     */
    return square(x) + cube(x);
}

/* Recursive functions are NOT inlined (infinite expansion) */
int fibonacci(int n)
{
    if (n <= 1) return n;
    return fibonacci(n-1) + fibonacci(n-2);
}

/* Large functions may not be inlined (code size cost) */
int large_function(int x)
{
    int result = 0;
    for (int i = 0; i < 100; i++) {
        result += x * i;
        result ^= (result >> 3);
        result += (result << 5);
    }
    return result;
}
