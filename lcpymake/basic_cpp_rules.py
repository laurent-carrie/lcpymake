import subprocess
from typing import List
from pathlib import Path
from lcpymake.rule import Rule
from lcpymake import logger
import re

# these are basic rules to scan, compile and link c++ code on linux


def scan_cpp(include_path):
    def _scan_cpp(filename):
        logger.info(f"scan {filename}")
        r = re.compile("#include +\"(.*)\".*")
        ret = []
        with open(str(filename), 'r') as fin:
            for line in fin.readlines():
                match = re.match(r, line)
                if match:
                    logger.info(f"found match {line}")
                    depfile = match.group(1)
                    for p in include_path:
                        d: Path = p / depfile
                        ret.append(d)

        return ret
    return _scan_cpp


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
        logger.info(f"run build {sources} {targets}")
        command2 = command(sources, targets)
        logger.info(command2)
        p: subprocess.CompletedProcess = subprocess.run(
            args=command2, check=False, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        if p.returncode != 0:
            logger.error(p.stdout)
            logger.error(p.stderr)
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
        return p.returncode == 0

    return Rule(info, run)
