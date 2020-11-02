from lcpymake import base
from pathlib import Path
from typing import List

import subprocess

import step1


def compile_rule(sources: List[Path], targets: List[Path]) -> base.Rule:
    # this is a rule : a function that takes sources and targets
    # sources and targets are in the so-called mount directory,
    # and returns a tuple : a string for information purpose,
    # and a function to run.
    # this function should return True on success and False on error
    assert len(sources) == 1
    source = sources[0]
    assert len(targets) == 1
    target = targets[0]
    command = f'gcc -o {str(target)} -c {str(source)}'

    def run():
        p: subprocess.CompletedProcess = subprocess.run(command)
        if p.returncode != 0:
            print(f'command {p.args}, returned {p.returncode}')
        return p.returncode == 0

    return base.Rule(info=command, run=run)


def link_rule(sources, targets):
    assert len(targets) == 1
    target = targets[0]
    sources_string = ' '.join([str(t) for t in sources])
    command = f'gcc -o {str(target)}  {sources_string}'

    def run():
        p: subprocess.CompletedProcess = subprocess.run(command)
        if p.returncode != 0:
            print(f'command {p.args}, returned {p.returncode}')
        return p.returncode == 0

    return base.Rule(info=command, run=run)


def main():

    # step 1 : we declare a build graph, using nodes and explicit rules
    # implementing implicit rules, rules and scanner will come later

    here = Path(__file__).parent

    g = base.Graph(sourcedir=here / 'src', builddir=here / 'build-step-2')

    # add source files
    g.add_source_node('foo.cpp')
    g.add_source_node('bar.cpp')
    g.add_source_node('missing-foo.cpp')

    # add built files
    g.add_built_node('foo.o')
    g.add_built_node('bar.o')
    g.add_built_node('hello')

    g.add_explicit_rule(sources=['bar.cpp'], targets=['bar.o'], rule=compile_rule)
    g.add_explicit_rule(sources=['foo.cpp'], targets=['foo.o'], rule=compile_rule)
    g.add_explicit_rule(sources=['foo.o', 'bar.o'], targets=['hello'], rule=link_rule)

    print('graph after adding rules')
    g.print()

    return g


if __name__ == '__main__':
    main()
