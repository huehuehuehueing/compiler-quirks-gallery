/*
 * Tail call optimization: recursive calls become jumps.
 *
 * When a function's last action is calling another function
 * (or itself), the call can become a jump, saving stack space.
 */

/* Tail-recursive factorial - can be optimized to a loop */
int factorial_tail(int n, int acc)
{
    if (n <= 1)
        return acc;
    /* Last action is the recursive call - tail position */
    return factorial_tail(n - 1, n * acc);
}

int factorial(int n)
{
    return factorial_tail(n, 1);
}

/* NOT tail recursive - multiplication after recursive call */
int factorial_not_tail(int n)
{
    if (n <= 1)
        return 1;
    /* Multiplication happens AFTER the call returns */
    return n * factorial_not_tail(n - 1);
}

/* Mutual tail recursion */
int is_even(unsigned n);
int is_odd(unsigned n);

int is_even(unsigned n)
{
    if (n == 0) return 1;
    return is_odd(n - 1);  /* Tail call */
}

int is_odd(unsigned n)
{
    if (n == 0) return 0;
    return is_even(n - 1);  /* Tail call */
}
