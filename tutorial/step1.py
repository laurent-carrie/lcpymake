from lcpymake import base
from pathlib import Path

# a rule that doesn't do anything


def dnr(sources, targets):
    return base.Rule('do nothing rule', lambda: None)


def main():

    # step 1 : we declare a build graph, using nodes and explicit rules
    # using implicit rules, implemeting rules and scanner will come later

    here = Path(__file__).parent

    # a build graph.
    # sourcedir is the root of the sources,
    # sandbox is where the build will take place.
    g = base.Graph(sourcedir=here / 'src', sandbox=here / 'build-step-1')

    # add source files
    g.add_source_node('foo.cpp')
    g.add_source_node('bar.cpp')
    g.add_source_node('missing-foo.cpp')

    # add built files
    g.add_built_node('foo.o')
    g.add_built_node('bar.o')
    g.add_built_node('hello')

    # print the graph
    # green are the source files
    # red are source files that don't exist (error !)
    # blue are built files
    g.print()

    # add explicit rules. For now, there is no code in the rule
    # it is just to build the graph
    g.add_explicit_rule(sources=['bar.cpp'], targets=['bar.o'], rule=dnr)
    g.add_explicit_rule(sources=['foo.cpp'], targets=['foo.o'], rule=dnr)
    g.add_explicit_rule(sources=['foo.o', 'bar.o'], targets=['hello'], rule=dnr)

    print('\n\n\n\n\ngraph after adding rules')
    g.print()


if __name__ == '__main__':
    main()
