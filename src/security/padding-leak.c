/*
 * Compiler-assisted information disclosure via struct padding
 * and stack slot reuse.
 *
 * Two realistic scenarios where compiler behavior causes sensitive
 * data to leak over the network:
 *
 *   1. Struct padding: a struct with poor field ordering has
 *      uninitialized padding bytes.  Assigning fields individually
 *      does NOT clear the gaps.  When the struct is sent as raw
 *      bytes, the padding carries whatever was on the stack before
 *      -- potentially secrets from a prior function call.
 *
 *   2. Stack reuse: the compiler reuses the same stack slot for
 *      locals in successive function calls.  If the second function
 *      only partially initializes its buffer before sending it,
 *      the tail still holds the first function's secret.
 *
 * Both vectors are invisible in the source code and only appear
 * when examining the compiled output.  The optimizer at -O2+
 * makes stack reuse more aggressive, widening the window.
 */
#include <string.h>

/* Opaque network send -- compiler cannot see through this,
 * so it cannot remove the call or reason about the buffer contents.
 * In a real program this would be send(fd, buf, len, 0).
 */
extern void transmit(const void *buf, unsigned len);


/* ================================================================
 * Example 1 — Struct padding leaks secret data
 * ================================================================
 *
 * bad_record has 6 bytes of padding due to alignment requirements:
 *
 *   Offset  Field/Padding
 *   ------  -------------
 *     0     role      (1 byte)
 *     1-3   PADDING   (3 bytes) -- never written!
 *     4-7   uid       (4 bytes)
 *     8     active    (1 byte)
 *     9-11  PADDING   (3 bytes) -- never written!
 *    12-15  gid       (4 bytes)
 *
 *   sizeof(bad_record) == 16, but only 10 bytes are meaningful.
 *   The 6 padding bytes contain whatever was on the stack.
 */
struct bad_record {
    char  role;       /* 1 byte  + 3 padding */
    int   uid;        /* 4 bytes             */
    char  active;     /* 1 byte  + 3 padding */
    int   gid;        /* 4 bytes             */
};  /* Total: 16 bytes, 6 bytes wasted as uninitialized padding */

/*
 * handle_login: processes a password into a stack-local buffer,
 * then returns.  The password bytes remain on the stack.
 */
void handle_login(const char *password)
{
    char secret_buf[64];
    strncpy(secret_buf, password, sizeof(secret_buf) - 1);
    secret_buf[sizeof(secret_buf) - 1] = '\0';

    /* ... authenticate ... (uses secret_buf) */
    /* The compiler considers secret_buf dead after this point.
     * No memset_s or explicit_bzero -- a common oversight.
     * The password bytes stay on the stack.
     */
}

/*
 * send_user_record: fills a bad_record field-by-field and transmits it.
 *
 * BUG: Field-by-field assignment does NOT touch the 6 padding bytes.
 * If this function's stack frame overlaps with handle_login's
 * (due to stack slot reuse), the padding bytes may still contain
 * fragments of the password.
 *
 * Compare the assembly at -O0 vs -O2: at -O2 the compiler may
 * place the struct in the same stack region as the prior call's
 * secret_buf, and there is no zeroing of the padding gaps.
 */
void send_user_record(int uid, int gid, char role, char active)
{
    struct bad_record rec;

    /* Each assignment writes only the field, not the padding */
    rec.role   = role;
    rec.uid    = uid;
    rec.active = active;
    rec.gid    = gid;

    /* Sends all 16 bytes including 6 bytes of uninitialized padding.
     * Those padding bytes may contain password fragments.
     */
    transmit(&rec, sizeof(rec));
}

/*
 * send_user_record_safe: zeroes the struct first, then assigns fields.
 *
 * FIX: memset clears the entire 16 bytes (including padding) before
 * any field assignment.  The padding bytes are now guaranteed to be 0.
 */
void send_user_record_safe(int uid, int gid, char role, char active)
{
    struct bad_record rec;
    memset(&rec, 0, sizeof(rec));   /* clears padding too */

    rec.role   = role;
    rec.uid    = uid;
    rec.active = active;
    rec.gid    = gid;

    transmit(&rec, sizeof(rec));
}


/* ================================================================
 * Example 2 — Stack reuse leaks prior function's secret
 * ================================================================
 *
 * decrypt_message writes a secret into a 128-byte local buffer.
 * log_network_event gets a 128-byte local buffer at the same
 * stack address (reuse), but only writes a short prefix into it
 * before sending the full 128 bytes over the network.
 *
 * The tail of the buffer still contains the decrypted plaintext.
 */

/* Opaque source of encrypted data -- compiler cannot inline this */
extern unsigned read_encrypted(void *dst, unsigned max_len);

void decrypt_message(const char *key)
{
    char plaintext[128];
    unsigned len = read_encrypted(plaintext, sizeof(plaintext));

    /* ... process the decrypted plaintext ... */
    /* len bytes of secret data sit in plaintext[0..len-1].
     * When this function returns, those bytes remain on the stack.
     */
    (void)len;
    (void)key;
}

/*
 * log_network_event: writes a short tag into a local buffer, then
 * sends the entire buffer to the network.
 *
 * BUG: Only the first ~14 bytes are initialized ("EVENT: ping\n").
 * The remaining ~114 bytes are whatever the compiler left in that
 * stack slot -- which is decrypt_message's plaintext if the compiler
 * reused the slot.
 *
 * At -O2+ the compiler aggressively reuses stack slots for locals
 * with non-overlapping lifetimes, making this overlap very likely.
 */
void log_network_event(const char *tag)
{
    char logbuf[128];

    /* Partial initialization -- only writes a few bytes */
    memcpy(logbuf, "EVENT: ", 7);
    strncpy(logbuf + 7, tag, sizeof(logbuf) - 8);
    logbuf[sizeof(logbuf) - 1] = '\0';

    /* Sends ALL 128 bytes, including ~114 uninitialized tail bytes
     * that may still hold the decrypted secret from decrypt_message.
     */
    transmit(logbuf, sizeof(logbuf));
}

/*
 * log_network_event_safe: initializes the full buffer before use.
 *
 * FIX: memset the entire buffer to zero before writing the tag.
 * The tail bytes are now guaranteed to be 0, not prior secrets.
 */
void log_network_event_safe(const char *tag)
{
    char logbuf[128];
    memset(logbuf, 0, sizeof(logbuf));

    memcpy(logbuf, "EVENT: ", 7);
    strncpy(logbuf + 7, tag, sizeof(logbuf) - 8);
    logbuf[sizeof(logbuf) - 1] = '\0';

    transmit(logbuf, sizeof(logbuf));
}
