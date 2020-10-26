from pathlib import Path
from typing import List,Callable
import subprocess

Rule = Callable[[ List[Path], List[Path]],subprocess.CompletedProcess]

class TargetNotGeneratedException(BaseException):
    def __init__(self,target:Path,process:subprocess.CompletedProcess):
        self.target = target
        self.process = process

def f(i,j):
    return i+j


def build_target(rule : Rule ,sources:List[Path],targets:List[Path]):
    for source in sources:
        if not source.exists():
            raise Exception(f"source does not exist : {source}")

    p = rule(sources,targets)

    if p.returncode != 0 :
        raise Exception(f"rule return code : {p.returncode}, command was {p.args}")

    for target in targets:
        if not target.exists():
            raise TargetNotGeneratedException(target,p)





def make_obj(sources: List[Path], targets: [Path]) -> subprocess.CompletedProcess :
    assert(len(sources)==1)
    assert(len(targets)==1)

    p = subprocess.run(['gcc', '-c','-o', str(targets[0]),str(sources[0])])

    return p