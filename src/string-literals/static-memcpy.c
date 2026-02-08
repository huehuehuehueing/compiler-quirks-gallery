#include <string.h>
#include <stdio.h>

void foo(void)
{
    char buf[5];

    memcpy(buf, "AAAA", 4);
    buf[sizeof(buf) - 1] = '\0';

    /* make sure the above is not treated as dead code */
    puts(buf);
}
