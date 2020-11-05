from pathlib import Path
import subprocess
# pylint:disable=E0401
import pytest
# pylint:enable=E0401
from lcpymake import api


def compile_rule(choice):
    def command(sources, targets):
        if choice == 'ok':
            return ['g++', '-o', str(targets[0]), '-c', str(sources[0])]
        if choice == 'bad target':
            return ['g++', '-o', str(targets[0].parent / 'toto.o'), '-c', str(sources[0])]
        if choice == 'bad command':
            return ['g++++++', '-o', str(targets[0].parent / 'toto.o'), '-c', str(sources[0])]
        raise ValueError(choice)

    def info(sources, targets):
        return ' '.join(command(sources, targets))

    def run(sources, targets):
        p: subprocess.CompletedProcess = subprocess.run(
            args=command(sources, targets), check=True)
        print(p.args)
        return p.returncode == 0

    return api.Rule(info, run)


cpp_compile: api.Rule = compile_rule('ok')
cpp_compile_bad_target: api.Rule = compile_rule('bad target')
cpp_compile_bad_command: api.Rule = compile_rule('bad command')


def link_rule():
    def command(sources, targets):
        return ['g++', '-o', str(targets[0])] + [str(s) for s in sources]

    def info(sources, targets):
        return ' '.join(command(sources, targets))

    def run(sources, targets):
        p: subprocess.CompletedProcess = subprocess.run(
            args=command(sources, targets), check=True)
        return p.returncode == 0

    return api.Rule(info, run)


cpp_link: api.Rule = link_rule()


# pylint:disable=R0201


class TestBuild:

    def test_build(self, datadir):
        g = api.create(srcdir=Path(datadir) / 'src', sandbox=Path(datadir) / 'sandbox')
        api.create_source_node(g, 'foo.cpp', scan=None)
        api.create_source_node(g, 'bar.cpp', scan=None)
        api.create_source_node(g, 'main.cpp', scan=None)
        api.create_built_node(g, artefacts=['foo.o'], sources=[
            'foo.cpp'], rule=cpp_compile)
        api.create_built_node(g, artefacts=['bar.o'], sources=[
            'bar.cpp'], rule=cpp_compile)
        api.create_built_node(g, artefacts=['main.o'], sources=[
            'main.cpp'], rule=cpp_compile)
        api.create_built_node(g, artefacts=['hello'], sources=[
            'main.o', 'foo.o', 'bar.o'], rule=cpp_link)

        j1 = [{'artefacts': ['foo.cpp'], 'scanned_deps': [], 'status': 'SOURCE_PRESENT'},
              {'artefacts': ['bar.cpp'], 'scanned_deps': [], 'status': 'SOURCE_PRESENT'},
              {'artefacts': ['main.cpp'], 'scanned_deps': [],
                  'status': 'SOURCE_PRESENT'},
              {'artefacts': ['foo.o'],
               'rule': 'g++ -o foo.o -c foo.cpp',
               'sources': ['foo.cpp'],
               'status': 'BUILT_MISSING'},
              {'artefacts': ['bar.o'],
               'rule': 'g++ -o bar.o -c bar.cpp',
               'sources': ['bar.cpp'],
               'status': 'BUILT_MISSING'},
              {'artefacts': ['main.o'],
               'rule': 'g++ -o main.o -c main.cpp',
               'sources': ['main.cpp'],
               'status': 'BUILT_MISSING'},
              {'artefacts': ['hello'],
               'rule': 'g++ -o hello main.o foo.o bar.o',
               'sources': ['main.o', 'foo.o', 'bar.o'],
               'status': 'BUILT_MISSING'}]
        assert api.to_json(g) == j1
        print()
        api.gprint(g)
        assert api.build(g)
        assert (Path(datadir) / 'sandbox/foo.o').exists()
        assert (Path(datadir) / 'sandbox/bar.o').exists()
        assert (Path(datadir) / 'sandbox/main.o').exists()
        assert (Path(datadir) / 'sandbox/hello').exists()

    def test_build_rule_does_not_produce_target(self, datadir):
        g = api.create(srcdir=Path(datadir) / 'src', sandbox=Path(datadir) / 'sandbox')
        api.create_source_node(g, 'foo.cpp', scan=None)
        api.create_built_node(g, artefacts=['foo.o'], sources=[
            'foo.cpp'], rule=cpp_compile_bad_target)
        print()
        api.gprint(g)
        with pytest.raises(api.TargetArtefactNotBuilt):
            api.build(g)

    def test_build_rule_fails(self, datadir):
        g = api.create(srcdir=Path(datadir) / 'src', sandbox=Path(datadir) / 'sandbox')
        api.create_source_node(g, 'foo.cpp', scan=None)
        api.create_built_node(g, artefacts=['foo.o'], sources=[
            'foo.cpp'], rule=cpp_compile_bad_command)
        print()
        api.gprint(g)
        with pytest.raises(api.RuleFailed):
            api.build(g)
