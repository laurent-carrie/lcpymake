from typing import List
import subprocess
import lcpymake.base
from pathlib import Path


def make_obj(sources: List[Path], targets: [Path]) -> subprocess.CompletedProcess:
    assert(len(sources) == 1)
    assert(len(targets) == 1)

    p = subprocess.run(['gcc', '-c', '-o', str(targets[0]), str(sources[0])])

    return p
