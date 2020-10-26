from lcpymake import base, gcc
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


class Test_1:

    def test_1(self, datadir):
        """
        test that the .o file is correctly generated
        """

        g = base.Graph(datadir)
        source_cpp = Path(datadir) / 'hello.cpp'
        target_cpp = Path(datadir) / 'hello.o'
        source_cpp2 = Path(datadir) / 'toto.cpp'
        target_cpp2 = Path(datadir) / 'toto.o'
        target_exe = Path(datadir) / 'hello.exe'
        g.add_rule(rule=gcc.make_obj, sources=[source_cpp], targets=[target_cpp])
        g.add_rule(rule=gcc.make_obj, sources=[source_cpp2], targets=[target_cpp2])
        g.add_rule(rule=gcc.make_exe, sources=[
                   target_cpp, target_cpp2], targets=[target_exe])

        g.draw('out.png')

    def test_2(self, datadir):
        """
        test that if a source does not exist, it will be caught
        """
        with pytest.raises(base.SourceNotFoundException):
            source = Path(datadir) / 'hello.x'
            target = Path(datadir) / 'hello.o'
            base.build_target(rule=gcc.make_obj, sources=[
                source], targets=[target])

    def test_3(self, datadir):
        """
        test that if the file is not generated, it will be caught
        """
        with pytest.raises(base.TargetNotGeneratedException):
            source = Path(datadir) / 'hello.cpp'
            target = Path(datadir) / 'hello.o'
            base.build_target(rule=wrong_make_obj, sources=[
                source], targets=[target])
