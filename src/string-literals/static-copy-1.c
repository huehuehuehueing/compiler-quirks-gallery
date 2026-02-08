/*
 * String copy with strcpy - compiler may inline as immediate stores.
 *
 * For small, known-length strings, strcpy becomes direct
 * memory stores with the string data embedded in instructions.
 */
#include <string.h>
#include <stdio.h>

void foo(void)
{
    char buf[100];
    strcpy(buf, "ABCDXXXXCCCC");

    /* Make observable to prevent dead code elimination */
    puts(buf);
}
