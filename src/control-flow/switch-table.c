/*
 * Switch optimization: jump tables vs. binary search vs. if-else.
 *
 * Compiler chooses implementation based on case distribution:
 * - Dense cases: jump table (O(1))
 * - Sparse cases: binary search (O(log n)) or if-else chain
 */

/* Dense cases - likely becomes a jump table */
int day_of_week(int day)
{
    switch (day) {
        case 0: return 'S';  /* Sunday */
        case 1: return 'M';
        case 2: return 'T';
        case 3: return 'W';
        case 4: return 'T';
        case 5: return 'F';
        case 6: return 'S';  /* Saturday */
        default: return '?';
    }
}

/* Sparse cases - likely if-else or binary search */
int sparse_switch(int x)
{
    switch (x) {
        case 1:     return 10;
        case 100:   return 20;
        case 10000: return 30;
        case 999999: return 40;
        default:    return 0;
    }
}

/* Two cases - becomes simple comparison */
int binary_choice(int x)
{
    switch (x) {
        case 0: return -1;
        case 1: return 1;
        default: return 0;
    }
}
