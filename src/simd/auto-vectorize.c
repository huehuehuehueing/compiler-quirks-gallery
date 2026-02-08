/*
 * Auto-vectorization: loops converted to SIMD operations.
 *
 * Compiler transforms scalar loops into vector operations
 * (SSE, AVX, NEON, etc.) processing multiple elements at once.
 */

/* Simple loop - prime candidate for vectorization */
void add_arrays(float *dst, const float *a, const float *b, int n)
{
    for (int i = 0; i < n; i++) {
        dst[i] = a[i] + b[i];
    }
    /* With -O3: becomes SIMD adds processing 4-8 floats at once */
}

/* Reduction - trickier to vectorize but often done */
float sum_array(const float *arr, int n)
{
    float sum = 0.0f;
    for (int i = 0; i < n; i++) {
        sum += arr[i];
    }
    return sum;
    /* May use horizontal add instructions or partial sums */
}

/* Loop with dependency - CANNOT be vectorized */
void fibonacci_array(int *arr, int n)
{
    arr[0] = 0;
    arr[1] = 1;
    for (int i = 2; i < n; i++) {
        /* Each iteration depends on previous two - serial */
        arr[i] = arr[i-1] + arr[i-2];
    }
}

/* Conditional in loop - may use masked operations */
void clamp_array(float *arr, int n, float min, float max)
{
    for (int i = 0; i < n; i++) {
        if (arr[i] < min) arr[i] = min;
        else if (arr[i] > max) arr[i] = max;
    }
}
