from typing import List
import subprocess
from lcpymake.base import subprocess_rule, Command
from pathlib import Path


@subprocess_rule
def make_obj(sources: List[Path], targets: [Path]) -> Command:
    assert(len(sources) == 1)
    assert(len(targets) == 1)

    return ['gcc', '-c', '-o', str(targets[0]), str(sources[0])]


@subprocess_rule
def make_exe(sources: List[Path], targets: [Path]) -> Command:
    assert(len(targets) == 1)

    command = ['gcc', '-o', str(targets[0])]
    command += [str(s) for s in sources]
    return command
