from pathlib import Path
import re

from lcpymake import api, logger
from lcpymake.basic_cpp_rules import link_rule, compile_rule, scan_cpp


def main():

    # step 1 : we declare a build graph, using nodes and explicit rules
    # using implicit rules, implementing rules and scanner will come later

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
                          'mylibs/foolib/foo.o', 'mylibs/barlib/bar.o', 'main.o'], rule=link_rule())

    # api.update_color_map(g,{"SOURCE_PRESENT": {"fg": 'White',"bg":"Red"}})

    return g
