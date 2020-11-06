from pathlib import Path
import re

from lcpymake import api
from tutorial.cpp_rules import cpp_compile, cpp_link


def scan_cpp(include_path):
    def inner_scan_cpp(filename):
        r = re.compile("#include +\"(.*)\".*")
        ret = []
        with open(str(filename), 'r') as fin:
            for line in fin.readlines():
                match = re.match(r, line)
                if match:
                    depfile = match.group(1)
                    for p in include_path:
                        if (p / depfile).exists():
                            ret.append(p / depfile)
                            break
                    else:
                        raise Exception(f'could not resolve dep {depfile}')
        print(ret)
        return ret
    return inner_scan_cpp


def main():

    # step 1 : we declare a build graph, using nodes and explicit rules
    # using implicit rules, implemeting rules and scanner will come later

    here = Path(__file__).parent

    # a build graph.
    # srcdir is the root of the sources,
    # sandbox is where the build will take place.
    srcdir = here / 'src'
    g = api.create(srcdir=srcdir, sandbox=here / 'build-step-2')

    # the scanner
    include_path = [srcdir / 'mylibs']

    # add source files
    api.create_source_node(g, artefact='mylibs/foolib/foo.cpp',
                           scan=scan_cpp(include_path))
    api.create_source_node(g, artefact='mylibs/barlib/bar.cpp',
                           scan=scan_cpp(include_path))

    # add built files
    api.create_built_node(g, artefacts=['mylibs/foolib/foo.o'],
                          sources=['mylibs/foolib/foo.cpp'], rule=cpp_compile)
    api.create_built_node(g, artefacts=['mylibs/foolib/bar.o'],
                          sources=['mylibs/barlib/bar.cpp'], rule=cpp_compile)
    api.create_built_node(g, artefacts=['hello'], sources=[
                          'mylibs/foolib/foo.o', 'mylibs/foolib/bar.o'], rule=cpp_link)

    return g
