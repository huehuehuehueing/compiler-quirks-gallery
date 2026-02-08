/*
 * Volatile prevents optimization of memory accesses.
 *
 * Without volatile, repeated reads/writes may be cached in
 * registers or eliminated. Volatile forces actual memory access.
 */

/* Hardware register simulation */
volatile int *const HARDWARE_REG = (volatile int *)0x40000000;

void write_hardware(int value)
{
    /* Each write MUST go to memory - cannot be cached or reordered */
    *HARDWARE_REG = value;
    *HARDWARE_REG = value;  /* Not eliminated - both writes happen */
}

int read_hardware(void)
{
    /* Each read MUST come from memory - cannot use cached value */
    int a = *HARDWARE_REG;
    int b = *HARDWARE_REG;
    return a + b;  /* Two actual memory reads */
}

/* Compare: non-volatile version */
int *non_volatile_ptr;

int read_non_volatile(void)
{
    /* Optimizer may read once and reuse the value */
    int a = *non_volatile_ptr;
    int b = *non_volatile_ptr;  /* May be optimized to: b = a */
    return a + b;
}
