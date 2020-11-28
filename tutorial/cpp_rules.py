import subprocess
from typing import List
from pathlib import Path
from lcpymake.rule import Rule


def compile_rule(include_path: List[Path]):
    def command(sources, targets):
        ret = ['g++', '-o', str(targets[0]), '-c', str(sources[0])]
        for p in include_path:
            ret.append('-I')
            ret.append(str(p))
        return ret

    def info(sources, targets):
        return ' '.join(command(sources, targets))

    def run(sources, targets):
        p: subprocess.CompletedProcess = subprocess.run(
            args=command(sources, targets), check=True)
        print(p.args)
        return p.returncode == 0

    return Rule(info, run)


def link_rule():
    def command(sources, targets):
        return ['g++', '-o', str(targets[0])] + [str(s) for s in sources]

    def info(sources, targets):
        return ' '.join(command(sources, targets))

    def run(sources, targets):
        p: subprocess.CompletedProcess = subprocess.run(
            args=command(sources, targets), check=True)
        print(p.args)
        return p.returncode == 0

    return Rule(info, run)
