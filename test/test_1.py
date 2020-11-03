from lcpymake import base
from pathlib import Path
import pytest
from typing import List
import subprocess
import string


def rule_1(sources, targets) -> base.Rule:
    def run():
        pass

    return base.Rule(info='blah blah', run=run)


def compile_rule(sources: List[Path], targets: List[Path]) -> base.Rule:
    assert len(sources) == 1
    source = sources[0]
    assert len(targets) == 1
    target = targets[0]
    command = ['g++', '-o', str(target), '-c', str(source)]

    def run():
        p: subprocess.CompletedProcess = subprocess.run(command)
        if p.returncode != 0:
            print(f'command {p.args}, returned {p.returncode}')
        return p.returncode == 0

    return base.Rule(info=' '.join(command), run=run)


def link_rule(sources, targets):
    assert len(targets) == 1
    target = targets[0]
    command = ['g++', '-o', str(target)] + [str(s) for s in sources]

    def run():
        p: subprocess.CompletedProcess = subprocess.run(command)
        if p.returncode != 0:
            print(f'command {p.args}, returned {p.returncode}')
        return p.returncode == 0

    return base.Rule(info=' '.join(command), run=run)


def ok_graph(g):
    g.add_source_node('foo.cpp')
    g.add_source_node('bar.cpp')
    g.add_source_node('hello.cpp')
    g.add_built_node('foo.o')
    g.add_built_node('bar.o')
    g.add_built_node('hello.o')
    g.add_built_node('hello')

    g.add_explicit_rule(sources=['foo.cpp'],
                        targets=['foo.o'], rule=compile_rule)
    g.add_explicit_rule(sources=['bar.cpp'],
                        targets=['bar.o'], rule=compile_rule)
    g.add_explicit_rule(sources=['hello.cpp'],
                        targets=['hello.o'], rule=compile_rule)

    g.add_explicit_rule(sources=['foo.o', 'bar.o', 'hello.o'],
                        targets=['hello'], rule=link_rule)

    assert g.to_json() == {'bar.cpp': {'is_source': True,
                                       'path': 'bar.cpp',
                                       'preds': [],
                                       'rule': None,
                                       'status': 'SOURCE_PRESENT'},
                           'bar.o': {'is_source': False,
                                     'path': 'bar.o',
                                     'preds': ['bar.cpp'],
                                     'rule': 'g++ -o bar.o -c bar.cpp',
                                     'status': 'BUILT_MISSING'},
                           'foo.cpp': {'is_source': True,
                                       'path': 'foo.cpp',
                                       'preds': [],
                                       'rule': None,
                                       'status': 'SOURCE_PRESENT'},
                           'foo.o': {'is_source': False,
                                     'path': 'foo.o',
                                     'preds': ['foo.cpp'],
                                     'rule': 'g++ -o foo.o -c foo.cpp',
                                     'status': 'BUILT_MISSING'},
                           'hello': {'is_source': False,
                                     'path': 'hello',
                                     'preds': ['foo.o', 'bar.o', 'hello.o'],
                                     'rule': 'g++ -o hello foo.o bar.o hello.o',
                                     'status': 'BUILT_MISSING'},
                           'hello.cpp': {'is_source': True,
                                         'path': 'hello.cpp',
                                         'preds': [],
                                         'rule': None,
                                         'status': 'SOURCE_PRESENT'},
                           'hello.o': {'is_source': False,
                                       'path': 'hello.o',
                                       'preds': ['hello.cpp'],
                                       'rule': 'g++ -o hello.o -c hello.cpp',
                                       'status': 'BUILT_MISSING'}}


class Test_1:

    def test_graph(self, datadir):
        g = base.Graph(sourcedir=(datadir), builddir=datadir / 'tmp')
        g.add_source_node('hello.cpp')
        g.add_source_node('titi.cpp')
        g.add_built_node('hello.o')
        g.add_built_node('titi.o')
        g.add_built_node('hello')

        j1 = {'hello': {'is_source': False,
                        'path': 'hello',
                        'preds': [],
                        'rule': None,
                        'status': 'BUILT_MISSING'},
              'hello.cpp': {'is_source': True,
                            'path': 'hello.cpp',
                            'preds': [],
                            'rule': None,
                            'status': 'SOURCE_PRESENT'},
              'hello.o': {'is_source': False,
                          'path': 'hello.o',
                          'preds': [],
                          'rule': None,
                          'status': 'BUILT_MISSING'},
              'titi.cpp': {'is_source': True,
                           'path': 'titi.cpp',
                           'preds': [],
                           'rule': None,
                           'status': 'SOURCE_PRESENT'},
              'titi.o': {'is_source': False,
                         'path': 'titi.o',
                         'preds': [],
                         'rule': None,
                         'status': 'BUILT_MISSING'}}
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
                        'rule': 'blah blah',
                        'status': 'BUILT_MISSING'},
              'hello.cpp': {'is_source': True,
                            'path': 'hello.cpp',
                            'preds': [],
                            'rule': None,
                            'status': 'SOURCE_PRESENT'},
              'hello.o': {'is_source': False,
                          'path': 'hello.o',
                          'preds': [],
                          'rule': None,
                          'status': 'BUILT_MISSING'},
              'titi.cpp': {'is_source': True,
                           'path': 'titi.cpp',
                           'preds': [],
                           'rule': None,
                           'status': 'SOURCE_PRESENT'},
              'titi.o': {'is_source': False,
                         'path': 'titi.o',
                         'preds': [],
                         'rule': None,
                         'status': 'BUILT_MISSING'}}
        assert g.to_json() == j2

        with pytest.raises(base.CannotAddEdgeItWouldMakeALoop):
            g.add_explicit_rule(sources=['hello'], targets=['hello.o'], rule=rule_1)

        assert g.to_json() == j2
        g.add_explicit_rule(sources=['hello.cpp'], targets=['hello.o'], rule=rule_1)
        g.add_explicit_rule(sources=['titi.cpp'], targets=['titi.o'], rule=rule_1)

        j3 = {'hello': {'is_source': False,
                        'path': 'hello',
                        'preds': ['hello.o', 'titi.o'],
                        'rule': 'blah blah',
                        'status': 'BUILT_MISSING'},
              'hello.cpp': {'is_source': True,
                            'path': 'hello.cpp',
                            'preds': [],
                            'rule': None,
                            'status': 'SOURCE_PRESENT'},
              'hello.o': {'is_source': False,
                          'path': 'hello.o',
                          'preds': ['hello.cpp'],
                          'rule': 'blah blah',
                          'status': 'BUILT_MISSING'},
              'titi.cpp': {'is_source': True,
                           'path': 'titi.cpp',
                           'preds': [],
                           'rule': None,
                           'status': 'SOURCE_PRESENT'},
              'titi.o': {'is_source': False,
                         'path': 'titi.o',
                         'preds': ['titi.cpp'],
                         'rule': 'blah blah',
                         'status': 'BUILT_MISSING'}}
        assert g.to_json() == j3

        with pytest.raises(base.NodeAlreadyHasARule):
            g.add_explicit_rule(sources=['hello.o', 'titi.o'],
                                targets=['hello'], rule=rule_1)

    def test_build(self, datadir):
        g = base.Graph(sourcedir=(datadir), builddir=datadir / 'tmp')
        ok_graph(g)
        g.build()
        assert g.to_json() == {'bar.cpp': {'is_source': True,
                                           'path': 'bar.cpp',
                                           'preds': [],
                                           'rule': None,
                                           'status': 'SOURCE_PRESENT'},
                               'bar.o': {'is_source': False,
                                         'path': 'bar.o',
                                         'preds': ['bar.cpp'],
                                         'rule': 'g++ -o bar.o -c bar.cpp',
                                         'status': 'BUILT_PRESENT'},
                               'foo.cpp': {'is_source': True,
                                           'path': 'foo.cpp',
                                           'preds': [],
                                           'rule': None,
                                           'status': 'SOURCE_PRESENT'},
                               'foo.o': {'is_source': False,
                                         'path': 'foo.o',
                                         'preds': ['foo.cpp'],
                                         'rule': 'g++ -o foo.o -c foo.cpp',
                                         'status': 'BUILT_PRESENT'},
                               'hello': {'is_source': False,
                                         'path': 'hello',
                                         'preds': ['foo.o', 'bar.o', 'hello.o'],
                                         'rule': 'g++ -o hello foo.o bar.o hello.o',
                                         'status': 'BUILT_PRESENT'},
                               'hello.cpp': {'is_source': True,
                                             'path': 'hello.cpp',
                                             'preds': [],
                                             'rule': None,
                                             'status': 'SOURCE_PRESENT'},
                               'hello.o': {'is_source': False,
                                           'path': 'hello.o',
                                           'preds': ['hello.cpp'],
                                           'rule': 'g++ -o hello.o -c hello.cpp',
                                           'status': 'BUILT_PRESENT'}}

    def test_build_unconnected(self, datadir):
        g = base.Graph(sourcedir=(datadir), builddir=datadir / 'tmp')
        ok_graph(g)
        g.remove_node('hello')
        assert g.to_json() == {'bar.cpp': {'is_source': True,
                                           'path': 'bar.cpp',
                                           'preds': [],
                                           'rule': None,
                                           'status': 'SOURCE_PRESENT'},
                               'bar.o': {'is_source': False,
                                         'path': 'bar.o',
                                         'preds': ['bar.cpp'],
                                         'rule': 'g++ -o bar.o -c bar.cpp',
                                         'status': 'BUILT_MISSING'},
                               'foo.cpp': {'is_source': True,
                                           'path': 'foo.cpp',
                                           'preds': [],
                                           'rule': None,
                                           'status': 'SOURCE_PRESENT'},
                               'foo.o': {'is_source': False,
                                         'path': 'foo.o',
                                         'preds': ['foo.cpp'],
                                         'rule': 'g++ -o foo.o -c foo.cpp',
                                         'status': 'BUILT_MISSING'},
                               'hello.cpp': {'is_source': True,
                                             'path': 'hello.cpp',
                                             'preds': [],
                                             'rule': None,
                                             'status': 'SOURCE_PRESENT'},
                               'hello.o': {'is_source': False,
                                           'path': 'hello.o',
                                           'preds': ['hello.cpp'],
                                           'rule': 'g++ -o hello.o -c hello.cpp',
                                           'status': 'BUILT_MISSING'}}

        g.build()
        assert g.to_json() == {'bar.cpp': {'is_source': True,
                                           'path': 'bar.cpp',
                                           'preds': [],
                                           'rule': None,
                                           'status': 'SOURCE_PRESENT'},
                               'bar.o': {'is_source': False,
                                         'path': 'bar.o',
                                         'preds': ['bar.cpp'],
                                         'rule': 'g++ -o bar.o -c bar.cpp',
                                         'status': 'BUILT_PRESENT'},
                               'foo.cpp': {'is_source': True,
                                           'path': 'foo.cpp',
                                           'preds': [],
                                           'rule': None,
                                           'status': 'SOURCE_PRESENT'},
                               'foo.o': {'is_source': False,
                                         'path': 'foo.o',
                                         'preds': ['foo.cpp'],
                                         'rule': 'g++ -o foo.o -c foo.cpp',
                                         'status': 'BUILT_PRESENT'},
                               'hello.cpp': {'is_source': True,
                                             'path': 'hello.cpp',
                                             'preds': [],
                                             'rule': None,
                                             'status': 'SOURCE_PRESENT'},
                               'hello.o': {'is_source': False,
                                           'path': 'hello.o',
                                           'preds': ['hello.cpp'],
                                           'rule': 'g++ -o hello.o -c hello.cpp',
                                           'status': 'BUILT_PRESENT'}}
