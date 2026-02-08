/*
 * Restrict pointers enable better optimization.
 *
 * The 'restrict' keyword promises that pointers don't alias,
 * allowing the compiler to optimize more aggressively.
 */

/* Without restrict - compiler must be conservative */
void copy_no_restrict(int *dst, const int *src, int n)
{
    /* dst and src MIGHT overlap, so compiler must handle that */
    for (int i = 0; i < n; i++) {
        dst[i] = src[i];
    }
}

/* With restrict - compiler knows no aliasing */
void copy_restrict(int *restrict dst, const int *restrict src, int n)
{
    /* dst and src guaranteed not to overlap
     * Compiler can use faster copy or vectorize freely
     */
    for (int i = 0; i < n; i++) {
        dst[i] = src[i];
    }
}

/* Multiplication example - dramatic difference */
void scale_no_restrict(float *result, const float *input,
                       const float *scale, int n)
{
    /* Compiler doesn't know if result aliases input or scale */
    for (int i = 0; i < n; i++) {
        result[i] = input[i] * (*scale);
    }
    /* Must reload *scale each iteration! */
}

void scale_restrict(float *restrict result,
                    const float *restrict input,
                    const float *restrict scale, int n)
{
    /* Compiler knows result doesn't alias scale */
    for (int i = 0; i < n; i++) {
        result[i] = input[i] * (*scale);
    }
    /* Can load *scale once and reuse */
}
