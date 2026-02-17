/*
 * Variable-Length Arrays (VLAs) allocate on the stack with no
 * bounds checking.  A user-controlled size can exhaust the stack
 * instantly, bypassing stack clash protection in some cases.
 *
 * At -O2+ the compiler may eliminate the VLA entirely if the
 * buffer is unused (dead store elimination), hiding the bug
 * during testing but crashing in production.
 *
 * Real-world: CVE-2024-1086 (Linux nftables VLA-related),
 * CERT MSC39-C advisory against VLAs.
 */
#include <string.h>

/* Observable sink - compiler cannot remove the buffer */
extern void process(const void *buf, unsigned len);

/* BUG: user-controlled VLA size, no upper bound */
void handle_packet_bad(const char *data, unsigned user_len)
{
    char buf[user_len];  /* stack allocation from untrusted input */
    memcpy(buf, data, user_len);
    process(buf, user_len);
}

/* SAFE: fixed maximum with heap fallback */
void handle_packet_safe(const char *data, unsigned user_len)
{
    char stack_buf[4096];
    char *buf = stack_buf;

    if (user_len > sizeof(stack_buf)) {
        return;  /* reject oversized input */
    }

    memcpy(buf, data, user_len);
    process(buf, user_len);
}
