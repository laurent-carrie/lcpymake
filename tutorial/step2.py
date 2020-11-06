from pathlib import Path

from lcpymake import api
from tutorial.cpp_rules import cpp_compile, cpp_link


def main():

    # step 1 : we declare a build graph, using nodes and explicit rules
    # using implicit rules, implemeting rules and scanner will come later

    here = Path(__file__).parent

    # a build graph.
    # srcdir is the root of the sources,
    # sandbox is where the build will take place.
    g = api.create(srcdir=here / 'src', sandbox=here / 'build-step-2')

    # add source files
    api.create_source_node(g, artefact='mylibs/foolib/foo.cpp', scan=None)
    api.create_source_node(g, artefact='mylibs/barlib/bar.cpp', scan=None)

    # add built files
    api.create_built_node(g, artefacts=['mylibs/foolib/foo.o'],
                          sources=['mylibs/foolib/foo.cpp'], rule=cpp_compile)
    api.create_built_node(g, artefacts=['mylibs/barlib/bar.o'],
                          sources=['mylibs/barlib/bar.cpp'], rule=cpp_compile)
    api.create_built_node(g, artefacts=['hello'], sources=[
                          'foo.o', 'bar.o'], rule=cpp_link)

    return g
