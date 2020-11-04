from pathlib import Path
import subprocess

from lcpymake import api


def compile_rule():
    def command(sources, targets):
        return ['g++', '-o', str(targets[0]), '-c', str(sources[0])]

    def info(sources, targets):
        return ' '.join(command(sources, targets))

    def run(sources, targets):
        p: subprocess.CompletedProcess = subprocess.run(
            args=command(sources, targets), check=True)
        print(p.args)
        return p.returncode == 0

    return api.Rule(info, run)


cpp_compile: api.Rule = compile_rule()


def link_rule():
    def command(sources, targets):
        return ['g++', '-o', str(targets[0])] + sources

    def info(sources, targets):
        return ' '.join(command(sources, targets))

    def run(sources, targets):
        p: subprocess.CompletedProcess = subprocess.run(
            args=command(sources, targets), check=True)
        print(p.args)
        return p.returncode == 0

    return api.Rule(info, run)


cpp_link: api.Rule = link_rule()


# pylint:disable=R0201


class TestBuild:

    def test_build(self, datadir):
        g = api.create(srcdir=Path(datadir) / 'src', sandbox=Path(datadir) / 'sandbox')
        api.create_source_node(g, 'foo.cpp')
        api.create_source_node(g, 'bar.cpp')
        api.create_source_node(g, 'main.cpp')
        api.create_built_node(g, artefacts=['foo.o'], sources=[
            'foo.cpp'], rule=cpp_compile)
        api.create_built_node(g, artefacts=['bar.o'], sources=[
            'bar.cpp'], rule=cpp_compile)
        api.create_built_node(g, artefacts=['main.o'], sources=[
            'main.cpp'], rule=cpp_compile)
        api.create_built_node(g, artefacts=['hello'], sources=[
            'main.o', 'foo.o', 'bar.o'], rule=cpp_link)

        j1 = [{'artefacts': ['foo.cpp'], 'status': 'SOURCE_PRESENT'},
              {'artefacts': ['bar.cpp'], 'status': 'SOURCE_PRESENT'},
              {'artefacts': ['main.cpp'], 'status': 'SOURCE_PRESENT'},
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
