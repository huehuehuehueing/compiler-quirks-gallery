/*
 * Static string initialization with concatenation.
 *
 * Adjacent string literals are concatenated at compile time.
 * The initializer may become a single memcpy or inline stores.
 */
#include <string.h>
#include <stdio.h>

void foo(void)
{
    /* Adjacent strings concatenated at compile time: "AAAABBBB" */
    char buf[100] = { "AAAA" "BBBB" };

    /* Make observable to prevent dead code elimination */
    puts(buf);
}
