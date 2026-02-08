/*
 * Infinite loop removed as undefined behavior.
 *
 * A loop with no side effects that doesn't terminate is UB.
 * Compiler may remove it entirely or assume it terminates.
 */

/* This function may not loop forever as expected! */
void spin_forever(void)
{
    /* No volatile, no side effects - UB if it never terminates.
     * Compiler may remove this entirely.
     */
    while (1)
        ;
}

/* Correct way to spin (e.g., for embedded busy-wait) */
void spin_forever_safe(void)
{
    /* volatile prevents optimization */
    while (1)
    {
        __asm__ volatile("" ::: "memory");
    }
}
