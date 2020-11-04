#include <iostream>
#include "bar.h"

extern void foo() ;




int main(int argc,char**argv ){
    std::cout << "hello world " << std::endl ;
    foo() ;
    bar() ;

}
