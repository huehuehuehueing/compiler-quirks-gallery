/*
 * Structure layout and padding optimizations.
 *
 * Compilers add padding for alignment but optimize access patterns.
 * Field reordering may be done with certain flags.
 */
#include <stddef.h>

/* Poor layout - lots of padding */
struct bad_layout {
    char a;       /* 1 byte + 3 padding */
    int b;        /* 4 bytes */
    char c;       /* 1 byte + 3 padding */
    int d;        /* 4 bytes */
};  /* Total: 16 bytes, 6 bytes wasted */

/* Good layout - minimal padding */
struct good_layout {
    int b;        /* 4 bytes */
    int d;        /* 4 bytes */
    char a;       /* 1 byte */
    char c;       /* 1 byte + 2 padding */
};  /* Total: 12 bytes, 2 bytes wasted */

/* Returns sizes - evaluate at compile time */
int get_bad_size(void)
{
    return sizeof(struct bad_layout);
}

int get_good_size(void)
{
    return sizeof(struct good_layout);
}

/* Offsetof shows where padding is */
int get_bad_c_offset(void)
{
    return offsetof(struct bad_layout, c);
}
