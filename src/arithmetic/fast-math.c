/*
 * Fast-math optimizations: -ffast-math / -Ofast effects.
 *
 * These flags allow the compiler to reorder floating-point
 * operations, assuming associativity (which floats don't have).
 * Can change results or break special value handling.
 */

/* With -ffast-math, this may be reordered and give different results */
float sum_array(const float *arr, int n)
{
    float sum = 0.0f;
    for (int i = 0; i < n; i++)
        sum += arr[i];
    return sum;
}

/* NaN check may be optimized away with -ffast-math */
int is_nan(float x)
{
    /* With -ffast-math, compiler assumes no NaN values exist,
     * so this comparison may be optimized to always return 0.
     */
    return x != x;
}

/* Division by variable may become multiplication by reciprocal */
float divide_by_y(float x, float y)
{
    /* With -ffast-math: may become x * (1.0f / y)
     * Less accurate but faster on some architectures.
     */
    return x / y;
}

/* Algebraic simplification (inexact with floats!) */
float algebraic(float a, float b, float c)
{
    /* With -ffast-math: (a + b) + c may be reordered to a + (b + c)
     * These can give different results with floating point!
     */
    return (a + b) + c;
}
