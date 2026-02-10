/* @gallery-hints
 *   extra-flags: -fstack-protector-all
 *   compiler-exclude: vc_v19_44_VS17_14_x64, vc_v19_44_VS17_14_x86
 */

/*
 * Stack Protector (Stack Canary)
 *
 * With -fstack-protector-all the compiler inserts a canary value
 * between local variables and the saved return address. Before the
 * function returns, the canary is checked; if it was overwritten
 * (e.g. by a buffer overflow), the program aborts.
 *
 * Look for: canary load from %fs:0x28 (or %gs:0x14 on 32-bit),
 * comparison before the function epilogue, and a call to
 * __stack_chk_fail on mismatch.
 */
#include <string.h>

void copy_input(const char *input)
{
    char buf[64];
    strcpy(buf, input);   /* intentionally unsafe for demonstration */
    (void)buf;
}
