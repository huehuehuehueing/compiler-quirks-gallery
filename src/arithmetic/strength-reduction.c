/*
 * Strength reduction: expensive operations replaced with cheaper ones.
 *
 * Multiplication by powers of 2 becomes shifts.
 * Division by constants becomes multiplication + shift.
 */

int multiply_by_8(int x)
{
    /* Becomes: x << 3 */
    return x * 8;
}

int multiply_by_15(int x)
{
    /* May become: (x << 4) - x */
    return x * 15;
}

unsigned divide_by_3(unsigned x)
{
    /* Division is expensive. Compiler uses "magic number" multiplication:
     * Becomes something like: (x * 0xAAAAAAAB) >> 33
     */
    return x / 3;
}

unsigned modulo_power_of_2(unsigned x)
{
    /* Becomes: x & 7 */
    return x % 8;
}
