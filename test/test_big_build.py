import re
from pathlib import Path
import subprocess

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


def scan_cpp(filename):
    r = re.compile("#include +\"(.*)\".*")
    ret = []
    with open(str(filename), 'r') as fin:
        for line in fin.readlines():
            match = re.match(r, line)
            if match:
                ret.append(match.group(1))
    return ret


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

        n = 200
        srcdir.mkdir(parents=True, exist_ok=True)
        with open(srcdir / 'main.cpp', 'w') as fout:
            fout.write('#include <iostream>\n')
            for i in range(n):
                fout.write(f"#include \"foo_{i}.h\"\n")
            fout.write('int main(int argc,char** argv) {\n')
            for i in range(n):
                fout.write(f'foo_{i}() ;\n')
            fout.write('return 0 ; \n}\n')

        for i in range(n):
            with open(srcdir / f'foo_{i}.h', 'w') as fout:
                fout.write(f'#ifndef foo_{i}_defined_\n')
                fout.write(f'#define foo_{i}_defined_ 1\n')
                fout.write(f'void foo_{i}() ;\n')
                fout.write('#endif\n')

        for i in range(n):
            with open(srcdir / f'foo_{i}.cpp', 'w') as fout:
                fout.write(f'void foo_{i}() {{ return ; }}')

        api.create_source_node(g, artefact='main.cpp', scan=scan_cpp)
        for i in range(n):
            api.create_source_node(g, artefact=f'foo_{i}.cpp', scan=scan_cpp)
            api.create_built_node(g, artefacts=[f'foo_{i}.o'], sources=[
                                  f'foo_{i}.cpp'], rule=compile_rule('ok'))

        api.create_built_node(g, artefacts=['main.o'], sources=[
                              'main.cpp'], rule=compile_rule('ok'))
        api.scan_artefacts(g)
        api.gprint(g)
        api.build(g)
