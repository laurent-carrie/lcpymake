from pathlib import Path

from lcpymake import api

# a rule that doesn't do anything


def do_nothing_rule():
    def info(sources, targets):
        print(sources)
        print(targets)
        return 'do nothing'

    def run(sources, targets):
        print(sources)
        print(targets)

    return api.Rule(info, run)


rule_1: api.Rule = do_nothing_rule()


def main():

    # step 1 : we declare a build graph, using nodes and explicit rules
    # using implicit rules, implemeting rules and scanner will come later

    here = Path(__file__).parent

    # a build graph.
    # srcdir is the root of the sources,
    # sandbox is where the build will take place.
    g = api.create(srcdir=here / 'src', sandbox=here / 'build-step-1')

    # add source files
    api.create_source_node(g, artefact='foo.cpp', scan=None)
    api.create_source_node(g, artefact='bar.cpp', scan=None)
    api.create_source_node(g, artefact='missing-foo.cpp', scan=None)

    # add built files
    api.create_built_node(g, artefacts=['foo.o'], sources=['foo.cpp'], rule=rule_1)
    api.create_built_node(g, artefacts=['bar.o'], sources=['bar.cpp'], rule=rule_1)
    api.create_built_node(g, artefacts=['hello'], sources=[
                          'foo.o', 'bar.o'], rule=rule_1)

    # print the graph
    # green are the source files
    # red are source files that don't exist (error !)
    # blue are built files
    api.gprint(g)


if __name__ == '__main__':
    main()
