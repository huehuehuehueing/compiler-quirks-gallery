/*
 * Security issue: memset() to clear sensitive data is removed
 * as dead code when the buffer is not used afterward.
 *
 * This is a real security vulnerability pattern - passwords
 * and keys may remain in memory after "clearing".
 */
#include <string.h>
#include <stdio.h>

void process_password(const char *password)
{
    char local_copy[64];

    /* Copy password for processing */
    strncpy(local_copy, password, sizeof(local_copy) - 1);
    local_copy[sizeof(local_copy) - 1] = '\0';

    /* Do something observable with the password (simulate auth check) */
    if (local_copy[0] == 's' && local_copy[1] == 'e' &&
        local_copy[2] == 'c' && local_copy[3] == 'r' &&
        local_copy[4] == 'e' && local_copy[5] == 't') {
        puts("Access granted");
    } else {
        puts("Access denied");
    }

    /* Security: clear the password from stack
     * BUG: This memset is often REMOVED by optimizer
     * because local_copy is not used afterward!
     */
    memset(local_copy, 0, sizeof(local_copy));
}

void test_password(void)
{
    process_password("secret");
}
