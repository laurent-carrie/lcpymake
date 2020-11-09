from typing import List
import subprocess
# from lcpymake.base import subprocess_rule, add_automatic_subprocess_rule, Command
from pathlib import Path


def make_obj(source: Path, target: Path):
    def command(source, target):
        return ['gcc', '-c', '-o', str(target), str(source)]
    return command


# add_automatic_subprocess_rule('.cpp', '.o', make_obj)


# @subprocess_rule
def make_exe(sources: List[Path], targets: [Path]):
    assert(len(targets) == 1)

    command = ['gcc', '-o', str(targets[0])]
    command += [str(s) for s in sources]
    return command
