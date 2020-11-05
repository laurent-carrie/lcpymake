from pathlib import Path
import subprocess
# pylint:disable=E0401
import pytest
# pylint:enable=E0401
from lcpymake import api

compile_counter = 0


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
        # pylint:disable=W0603
        global compile_counter
        # pylint:enable=W0603
        compile_counter += 1
        print(f'compile counter : {compile_counter}')
        p: subprocess.CompletedProcess = subprocess.run(
            args=command(sources, targets), check=True)
        print(p.args)
        return p.returncode == 0

    return api.Rule(info, run)


cpp_compile: api.Rule = compile_rule('ok')
cpp_compile_bad_target: api.Rule = compile_rule('bad target')
cpp_compile_bad_command: api.Rule = compile_rule('bad command')


link_counter = 0


def link_rule():
    def command(sources, targets):
        return ['g++', '-o', str(targets[0])] + [str(s) for s in sources]

    def info(sources, targets):
        return ' '.join(command(sources, targets))

    def run(sources, targets):
        # pylint:disable=W0603
        global link_counter
        # pylint:enable=W0603
        link_counter += 1
        p: subprocess.CompletedProcess = subprocess.run(
            args=command(sources, targets), check=True)
        return p.returncode == 0

    return api.Rule(info, run)


cpp_link: api.Rule = link_rule()


# pylint:disable=R0201


class TestBuild:

    def test_build(self, datadir):
        srcdir = Path(datadir) / 'src'
        sandbox = Path(datadir) / 'sandbox'
        g = api.create(srcdir=srcdir, sandbox=sandbox)
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
               'digest': None,
               'ok_build': None,
               'rule': 'g++ -o foo.o -c foo.cpp',
               'sources': ['foo.cpp'],
               'status': 'BUILT_MISSING'},
              {'artefacts': ['bar.o'],
               'digest': None,
               'ok_build': None,
               'rule': 'g++ -o bar.o -c bar.cpp',
               'sources': ['bar.cpp'],
               'status': 'BUILT_MISSING'},
              {'artefacts': ['main.o'],
               'digest': None,
               'ok_build': None,
               'rule': 'g++ -o main.o -c main.cpp',
               'sources': ['main.cpp'],
               'status': 'BUILT_MISSING'},
              {'artefacts': ['hello'],
               'digest': None,
               'ok_build': None,
               'rule': 'g++ -o hello main.o foo.o bar.o',
               'sources': ['main.o', 'foo.o', 'bar.o'],
               'status': 'BUILT_MISSING'}]
        assert api.to_json(g) == j1
        print()
        api.gprint(g)
        # pylint:disable=W0603
        global compile_counter
        # pylint:enable=W0603
        compile_counter = 0
        assert api.build(g)
        assert compile_counter == 3
        assert (Path(datadir) / 'sandbox/foo.o').exists()
        assert (Path(datadir) / 'sandbox/bar.o').exists()
        assert (Path(datadir) / 'sandbox/main.o').exists()
        assert (Path(datadir) / 'sandbox/hello').exists()
        j2 = [{'artefacts': ['foo.cpp'], 'scanned_deps': [], 'status': 'SOURCE_PRESENT'},
              {'artefacts': ['bar.cpp'], 'scanned_deps': [], 'status': 'SOURCE_PRESENT'},
              {'artefacts': ['main.cpp'], 'scanned_deps': [],
                  'status': 'SOURCE_PRESENT'},
              {'artefacts': ['foo.o'],
               'digest': '7c2a7922e50668f6df5775add8fd477f0099345cb86e497cc9f3794d35ca109a',
               'ok_build': '7c2a7922e50668f6df5775add8fd477f0099345cb86e497cc9f3794d35ca109a',
               'rule': 'g++ -o foo.o -c foo.cpp',
               'sources': ['foo.cpp'],
               'status': 'BUILT_PRESENT'},
              {'artefacts': ['bar.o'],
               'digest': '8889d07b4228ca36076140099233151e5941d98aabb371ce79f91bafae93def5',
               'ok_build': '8889d07b4228ca36076140099233151e5941d98aabb371ce79f91bafae93def5',
               'rule': 'g++ -o bar.o -c bar.cpp',
               'sources': ['bar.cpp'],
               'status': 'BUILT_PRESENT'},
              {'artefacts': ['main.o'],
               'digest': 'cdd4277c43b2aa8ecfb314dfd47b78f5b8c8dfdbac9d39c67ddf1d868cf11cdf',
               'ok_build': 'cdd4277c43b2aa8ecfb314dfd47b78f5b8c8dfdbac9d39c67ddf1d868cf11cdf',
               'rule': 'g++ -o main.o -c main.cpp',
               'sources': ['main.cpp'],
               'status': 'BUILT_PRESENT'},
              {'artefacts': ['hello'],
               'digest': 'ae1445ce786df7decc8e6b757f2f047692857c660696dc568bcad73928d9bd16',
               'ok_build': 'ae1445ce786df7decc8e6b757f2f047692857c660696dc568bcad73928d9bd16',
               'rule': 'g++ -o hello main.o foo.o bar.o',
               'sources': ['main.o', 'foo.o', 'bar.o'],
               'status': 'BUILT_PRESENT'}]

        # test that rebuild does not do anything, thanks to digest
        compile_counter = 0
        api.build(g)
        assert compile_counter == 0

        # change a file, check that there is a compilation, but not propagated
        text = (Path(srcdir) / 'main.cpp').read_text() + \
            '\n// some comment to change digest of file'
        (Path(srcdir) / 'main.cpp').write_text(text)
        j3 = api.to_json(g)
        assert j2[5]['artefacts'] == ['main.o']
        assert j3[5]['artefacts'] == ['main.o']
        assert j2[5]['ok_build'] == j3[5]['ok_build']
        assert j2[5]['digest'] != j3[5]['digest']

        # pylint:disable=W0603
        global link_counter
        # pylint:enable=W0603

        compile_counter = 0
        link_counter = 0
        api.build(g)
        # check that only one file wash compiled
        assert compile_counter == 1
        # check that link was not rerun
        assert link_counter == 0

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
