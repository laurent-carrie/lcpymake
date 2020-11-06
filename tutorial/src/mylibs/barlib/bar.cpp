#include <iostream>
// I know, it should be <time.h>, but it is to test the scanner
#include <time.h>
#include "barlib/bar.h"

int bar(int i) {
    time_t rawtime;
    struct tm * timeinfo;

    time ( &rawtime );
    timeinfo = localtime ( &rawtime );
    printf ( "The current date/time is: %s", asctime (timeinfo) );

    return i ;
}
