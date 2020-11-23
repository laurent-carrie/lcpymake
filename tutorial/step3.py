from pathlib import Path
import re

from lcpymake import api
from tutorial.cpp_rules import cpp_link, compile_rule


def scan_cpp(include_path):
    def _scan_cpp(filename):
        r = re.compile("#include +\"(.*)\".*")
        ret = []
        with open(str(filename), 'r') as fin:
            for line in fin.readlines():
                match = re.match(r, line)
                if match:
                    depfile = match.group(1)
                    for p in include_path:
                        d: Path = p / depfile
                        if not d.exists():
                            continue
                        ret.append(d)

        return ret
    return _scan_cpp


def main():

    # step 1 : we declare a build graph, using nodes and explicit rules
    # using implicit rules, implemeting rules and scanner will come later

    here = Path(__file__).parent

    # a build graph.
    # srcdir is the root of the sources,
    # sandbox is where the build will take place.
    srcdir = here / 'src'
    sandbox = here / 'build-step-3'
    g = api.create(srcdir=srcdir, sandbox=sandbox)

    # for the scanner, and the compile command
    include_path_scan = [srcdir / 'mylibs']
    include_path_compile = [sandbox / 'mylibs']

    # add source files
    api.create_source_node(g, artefact='mylibs/foolib/foo.cpp',
                           scan=scan_cpp(include_path_scan))
    api.create_source_node(g, artefact='mylibs/barlib/bar.cpp',
                           scan=scan_cpp(include_path_scan))
    api.create_source_node(g, artefact='main.cpp',
                           scan=scan_cpp(include_path_scan))

    # add built files
    api.create_built_node(g, artefacts=['mylibs/foolib/foo.o'],
                          sources=['mylibs/foolib/foo.cpp'],
                          rule=compile_rule(include_path_compile))
    api.create_built_node(g, artefacts=['mylibs/barlib/bar.o'],
                          sources=['mylibs/barlib/bar.cpp'],
                          rule=compile_rule(include_path_compile))
    api.create_built_node(g, artefacts=['main.o'],
                          sources=['main.cpp'], rule=compile_rule(include_path_compile))

    api.create_built_node(g, artefacts=['hello'], sources=[
                          'mylibs/foolib/foo.o', 'mylibs/barlib/bar.o', 'main.o'], rule=cpp_link)

    # api.update_color_map(g,{"SOURCE_PRESENT": {"fg": 'White',"bg":"Red"}})

    return g
