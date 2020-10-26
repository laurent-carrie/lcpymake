from lcpymake import a
from pathlib import Path
import pytest
from typing import List
import subprocess


def func(x):
    return x + 1

def wrong_make_obj(sources: List[Path], targets: [Path]) -> subprocess.CompletedProcess :
    assert(len(sources)==1)
    assert(len(targets)==1)

    p = subprocess.run(['gcc', '-c','-o', str(targets[0].with_suffix(".x")),str(sources[0])])

    return p

class Test_generate_o:

    def test_1(self,datadir):
        """
        test that the .o file is correctly generated
        """

        source = Path(datadir) / "hello.cpp"
        target = Path("hello.o")
        a.build_target(rule=a.make_obj,sources=[source],targets=[target])


    def test_2(self,datadir):
        """
        test that if the file is not generated, it will be caught
        """
        with pytest.raises(a.TargetNotGeneratedException):
            source = Path(datadir) / "hello.cpp"
            target = Path("hello.o")
            a.build_target(rule=wrong_make_obj, sources=[source], targets=[target])