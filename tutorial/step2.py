from pathlib import Path

from lcpymake import api
from tutorial.cpp_rules import compile_rule, link_rule


def main():
    # step 1 : we declare a build graph, using nodes and explicit rules
    # using implicit rules, implemeting rules and scanner will come later

    here = Path(__file__).parent

    # a build graph.
    # srcdir is the root of the sources,
    srcdir = here / 'src'
    sandbox = here / 'build-step-2'

    # sandbox is where the build will take place.
    g = api.create(srcdir=srcdir, sandbox=sandbox)

    # it is tempting to use srcdir instead of sandbox
    # ... avoid that, the build would mixup srcdir and sandbox
    include_path = [sandbox / 'mylibs']

    # add source files
    api.create_source_node(g, artefact='mylibs/foolib/foo.cpp', scan=None)
    api.create_source_node(g, artefact='mylibs/barlib/bar.cpp', scan=None)
    # api.create_source_node(g, artefact='mylibs/foolib/foo.h', scan=None)
    # api.create_source_node(g, artefact='mylibs/barlib/bar.h', scan=None)

    # add built files
    api.create_built_node(g, artefacts=['mylibs/foolib/foo.o'],
                          sources=['mylibs/foolib/foo.cpp'], rule=compile_rule(include_path))
    api.create_built_node(g, artefacts=['mylibs/barlib/bar.o'],
                          sources=['mylibs/barlib/bar.cpp'], rule=compile_rule(include_path))
    api.create_built_node(g, artefacts=['hello'],
                          sources=[
                              'mylibs/foolib/foo.o',
                              'mylibs/barlib/bar.o'], rule=link_rule())

    return g
