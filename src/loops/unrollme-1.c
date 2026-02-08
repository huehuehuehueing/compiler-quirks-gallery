void foo(void)
{
    int i;
    char buf[8];

    for (i = 0; i < sizeof(buf); i++)
    {
        buf[i] = 'A';
    }

    /* the above should all be optimized out */
}