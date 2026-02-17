/*
 * Dead code elimination after _Noreturn / __attribute__((noreturn)).
 *
 * When the compiler knows a function never returns, all code after
 * the call is eliminated.  If the function CAN actually return
 * (buggy annotation), execution falls into whatever follows in
 * memory -- potentially the next function's code.
 *
 * Real-world: Misannotated panic/abort wrappers in kernel code.
 */
#include <stdlib.h>

/* Correctly annotated: abort() is _Noreturn */
void handle_fatal_correct(int code)
{
    /* cleanup ... */
    (void)code;
    abort();
    /* Compiler eliminates everything below -- correct, abort never returns */
}

/* Misannotated: my_log is NOT noreturn but declared as such */
__attribute__((noreturn)) void my_log(const char *msg);

void handle_error_bad(int code)
{
    if (code < 0) {
        my_log("error occurred");
        /* Compiler assumes my_log never returns.
         * All code after this point is dead-code-eliminated.
         * If my_log DOES return, execution falls through to
         * whatever the linker placed next in memory.
         */
    }
    /* This cleanup code may be eliminated entirely */
    code = 0;
}
