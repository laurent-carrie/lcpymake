#include <string>
#include <iostream>

std::string make_greeting_string() {
    return "hello world" ;
}

int main(int argc,char** argv) {
    std::cout << make_greeting_string() << std::endl ;
    return 0 ;
}
