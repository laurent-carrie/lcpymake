import subprocess
import lcpymake.api as api


def compile_rule():
    def command(sources, targets):
        return ['g++', '-o', str(targets[0]), '-c', str(sources[0])]

    def info(sources, targets):
        return ' '.join(command(sources, targets))

    def run(sources, targets):
        p: subprocess.CompletedProcess = subprocess.run(
            args=command(sources, targets), check=True)
        print(p.args)
        return p.returncode == 0

    return api.Rule(info, run)


cpp_compile: api.Rule = compile_rule()


def link_rule():
    def command(sources, targets):
        return ['g++', '-o', str(targets[0])] + sources

    def info(sources, targets):
        return ' '.join(command(sources, targets))

    def run(sources, targets):
        p: subprocess.CompletedProcess = subprocess.run(
            args=command(sources, targets), check=True)
        print(p.args)
        return p.returncode == 0

    return api.Rule(info, run)


cpp_link: api.Rule = link_rule()
