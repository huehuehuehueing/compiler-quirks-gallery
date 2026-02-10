/* @gallery-hints
 *   extra-flags: -D_FORTIFY_SOURCE=2
 *   compiler-only: cg152, clang1910
 *   scenario-exclude: O0
 */

/*
 * FORTIFY_SOURCE with sprintf / snprintf
 *
 * _FORTIFY_SOURCE replaces sprintf with __sprintf_chk which knows the
 * destination buffer size. If the formatted string would overflow, the
 * program aborts instead of silently corrupting memory.
 *
 * Look for: calls to __sprintf_chk or __snprintf_chk rather than
 * plain sprintf / snprintf.
 */
#include <stdio.h>

void format_message(char *buf, int bufsize, int code)
{
    /* FORTIFY_SOURCE turns this into __sprintf_chk with the
     * known object size of buf (if derivable). */
    sprintf(buf, "error %d occurred", code);
}

void bounded_format(char *buf, int bufsize, const char *name)
{
    snprintf(buf, bufsize, "Hello, %s!", name);
}
