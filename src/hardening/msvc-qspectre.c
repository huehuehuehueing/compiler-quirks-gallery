/* @gallery-hints
 *   replace-flags: /O2 /Qspectre
 *   compiler-only: vc_v19_44_VS17_14_x64, vc_v19_44_VS17_14_x86
 */

/*
 * MSVC Spectre v1 Mitigation (/Qspectre)
 *
 * Spectre variant 1 exploits speculative execution past bounds
 * checks to leak data through cache side channels.  /Qspectre
 * inserts LFENCE instructions after conditional branches that
 * guard array accesses, serialising the pipeline so the
 * speculative path cannot leak secrets.
 *
 * MSVC offers three tiers (each a separate flag):
 *   /Qspectre          - LFENCE after recognised bounds-check
 *                        patterns (this file).
 *   /Qspectre-load     - LFENCE after every memory load; replaces
 *                        RET with  POP r11; LFENCE; JMP r11.
 *   /Qspectre-load-cf  - Like /Qspectre-load but only on loads in
 *                        control-flow-dependent paths.
 *
 * No GCC/Clang exact equivalent; Clang has
 * -mspeculative-load-hardening (different strategy), and GCC has
 * retpoline (-mindirect-branch=thunk) for indirect branches.
 *
 * Look for: LFENCE after the conditional branch that checks
 * index < size.
 */
#include <stddef.h>

/* Classic Spectre v1 gadget: bounds-check + dependent load. */
unsigned char lookup_table[256 * 512];

unsigned char spectre_gadget(unsigned char *array, size_t size,
                             size_t index)
{
    if (index < size)
    {
        /* Without /Qspectre the CPU may speculatively execute this
         * load before the branch resolves, leaking array[index]
         * through the cache.  /Qspectre adds an LFENCE before
         * the dependent load to prevent this. */
        unsigned char value = array[index];
        return lookup_table[value * 512];
    }
    return 0;
}
