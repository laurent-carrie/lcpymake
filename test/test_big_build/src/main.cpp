#include <iostream>

extern void foo() ;
extern void bar() ;


int main(int argc,char**argv ){
    std::cout << "hello world " << std::endl ;
    foo() ;
    bar() ;

}
