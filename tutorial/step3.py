from lcpymake import base
from pathlib import Path
from typing import List

import subprocess

import step2


def main():

    # we reuse the build graph and the rules of step2
    # and we run the build
    g = step2.main()

    # we remove this volontary error for the tutorial
    g.remove_node('missing-foo.cpp')
    g.print()

    g.builddir = Path(__file__).parent / 'build_step3'

    # build. this will first copy sources to the build directory (so called mount),
    # and then walk the tree and run the commands
    g.build()


if __name__ == '__main__':
    main()
