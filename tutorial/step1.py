from lcpymake import base
from pathlib import Path


def main():

    here = Path(__file__).parent

    # a build graph.
    # sourcedir is the root of the sources,
    # builddir is where the build will take place.
    g = base.Graph(sourcedir=here / 'src', builddir=here / 'build-step-1')

    # add source files
    g.add_source_node('hello.cpp')
    g.add_source_node('titi.cpp')

    # add built files
    g.add_built_node('hello.o')
    g.add_built_node('titi.o')
    g.add_built_node('hello')

    # print the graph
    # green are the source files
    # red are source files that don't exist (error !)
    # blue are built files
    g.print()

    # add explicit rules. For now, there is no code in the rule
    # it is just to build the graph
    g.add_explicit_rule(sources=['hello.cpp'], targets=['hello.o'], rule=None)
    g.add_explicit_rule(sources=['titi.cpp'], targets=['titi.o'], rule=None)
    g.add_explicit_rule(sources=['hello.o', 'titi.o'], targets=['hello'], rule=None)

    print('graph after adding rules')
    g.print()


if __name__ == '__main__':
    main()
