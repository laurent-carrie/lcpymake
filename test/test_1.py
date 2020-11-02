from lcpymake import base, gcc, plot
from pathlib import Path
import pytest
from typing import List
import subprocess


def func(x):
    return x + 1


def wrong_make_obj(sources: List[Path], targets: [Path]) -> subprocess.CompletedProcess:
    assert (len(sources) == 1)
    assert (len(targets) == 1)

    p = subprocess.run(
        ['gcc', '-c', '-o', str(targets[0].with_suffix('.x')), str(sources[0])])

    return p


def rule_1(sources, targets):
    return base.Rule(info='blah blah', run=None)


class Test_1:

    def test_1(self, datadir):
        g = base.Graph(sourcedir=(datadir), builddir=None)
        g.add_source_node('hello.cpp')
        g.add_source_node('titi.cpp')
        g.add_built_node('hello.o')
        g.add_built_node('titi.o')
        g.add_built_node('hello')

        with pytest.raises(base.NodeAlreadyThere):
            g.add_source_node('hello.cpp')

        with pytest.raises(base.CannotAddARuleForASourceNode):
            g.add_explicit_rule(sources=['hello.o'], targets=['hello.cpp'], rule=None)

        g.add_explicit_rule(sources=['hello.o', 'titi.o'], targets=['hello'], rule=None)

        with pytest.raises(base.CannotAddEdgeItWouldMakeALoop):
            g.add_explicit_rule(sources=['hello'], targets=['hello.o'], rule=None)

        g.add_explicit_rule(sources=['hello.cpp'], targets=['hello.o'], rule=None)
        g.add_explicit_rule(sources=['titi.cpp'], targets=['titi.o'], rule=None)

        with pytest.raises(base.NodeAlreadyHasARule):
            g.add_explicit_rule(sources=['hello.o', 'titi.o'],
                                targets=['hello'], rule=rule_1)

        g.print()
