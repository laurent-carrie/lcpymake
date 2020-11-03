from lcpymake import base, gcc, plot
from pathlib import Path
import pytest
from typing import List
import subprocess


def rule_1(sources, targets) -> base.Rule:
    def run():
        pass

    return base.Rule(info='blah blah', run=run)


class Test_1:

    def test_1(self, datadir):
        g = base.Graph(sourcedir=(datadir), builddir=datadir / 'tmp')
        g.add_source_node('hello.cpp')
        g.add_source_node('titi.cpp')
        g.add_built_node('hello.o')
        g.add_built_node('titi.o')
        g.add_built_node('hello')

        j1 = {'hello': {'is_source': False, 'path': 'hello', 'preds': [], 'rule': None},
              'hello.cpp': {'is_source': True,
                            'path': 'hello.cpp',
                            'preds': [],
                            'rule': None},
              'hello.o': {'is_source': False, 'path': 'hello.o', 'preds': [], 'rule': None},
              'titi.cpp': {'is_source': True, 'path': 'titi.cpp', 'preds': [], 'rule': None},
              'titi.o': {'is_source': False, 'path': 'titi.o', 'preds': [], 'rule': None}}
        assert g.to_json() == j1

        with pytest.raises(base.NodeAlreadyThere):
            g.add_source_node('hello.cpp')
        assert g.to_json() == j1

        with pytest.raises(base.CannotAddARuleForASourceNode):
            g.add_explicit_rule(sources=['hello.o'], targets=['hello.cpp'], rule=rule_1)
        assert g.to_json() == j1

        g.add_explicit_rule(sources=['hello.o', 'titi.o'],
                            targets=['hello'], rule=rule_1)
        j2 = {'hello': {'is_source': False,
                        'path': 'hello',
                        'preds': ['hello.o', 'titi.o'],
                        'rule': 'blah blah'},
              'hello.cpp': {'is_source': True,
                            'path': 'hello.cpp',
                            'preds': [],
                            'rule': None},
              'hello.o': {'is_source': False, 'path': 'hello.o', 'preds': [], 'rule': None},
              'titi.cpp': {'is_source': True, 'path': 'titi.cpp', 'preds': [], 'rule': None},
              'titi.o': {'is_source': False, 'path': 'titi.o', 'preds': [], 'rule': None}}
        assert j2 == g.to_json()

        with pytest.raises(base.CannotAddEdgeItWouldMakeALoop):
            g.add_explicit_rule(sources=['hello'], targets=['hello.o'], rule=rule_1)

        assert g.to_json() == j2
        g.add_explicit_rule(sources=['hello.cpp'], targets=['hello.o'], rule=rule_1)
        g.add_explicit_rule(sources=['titi.cpp'], targets=['titi.o'], rule=rule_1)

        j3 = {'hello': {'is_source': False,
                        'path': 'hello',
                        'preds': ['hello.o', 'titi.o'],
                        'rule': 'blah blah'},
              'hello.cpp': {'is_source': True,
                            'path': 'hello.cpp',
                            'preds': [],
                            'rule': None},
              'hello.o': {'is_source': False,
                          'path': 'hello.o',
                          'preds': ['hello.cpp'],
                          'rule': 'blah blah'},
              'titi.cpp': {'is_source': True, 'path': 'titi.cpp', 'preds': [], 'rule': None},
              'titi.o': {'is_source': False,
                         'path': 'titi.o',
                         'preds': ['titi.cpp'],
                         'rule': 'blah blah'}}
        assert g.to_json() == j3

        with pytest.raises(base.NodeAlreadyHasARule):
            g.add_explicit_rule(sources=['hello.o', 'titi.o'],
                                targets=['hello'], rule=rule_1)
