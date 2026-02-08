#include <stdio.h>

void foo(void)
{
    int i;
    char buf[8];

    for (i = 0; i < sizeof(buf); i++)
    {
        buf[i] = 'A';
    }

    /*
     * by dereferencing buf this should force the compile to NOT
     * eliminate the above as dead code. loop will likely still
     * be unrolled
     */
    printf("%s", buf);
}