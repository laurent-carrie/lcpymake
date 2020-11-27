from pathlib import Path
import pytest
from lcpymake import api
from lcpymake import rule


def dummy():
    def info(sources, targets):
        info = f'build target {[str(t) for t in targets]} from sources {[str(s) for s in sources]}'
        return info

    def run(sources, targets):
        print(sources)
        print(targets)

    return rule.Rule(info=info, run=run)


dummy_rule = dummy()


class TestGraph:

    def test_graph(self, datadir):
        g = api.create(srcdir=Path(datadir) / 'src', sandbox=Path(datadir) / 'sandbox')
        api.create_source_node(g, 'foo.cpp', scan=None)
        api.create_source_node(g, 'bar.cpp', scan=None)
        api.create_source_node(g, 'main.cpp', scan=None)
        api.create_built_node(g, artefacts=['foo.o'], sources=[
            'foo.cpp'], rule=dummy_rule)
        api.create_built_node(g, artefacts=['bar.o'], sources=[
            'bar.cpp'], rule=dummy_rule)
        api.create_built_node(g, artefacts=['main.o'], sources=[
            'main.cpp'], rule=dummy_rule)
        api.create_built_node(g, artefacts=['hello'], sources=[
            'main.o', 'bar.o', 'foo.o'], rule=dummy_rule)

        assert not g.is_built
        g.source_nodes
        assert g.is_built

        assert len(g.nodes) == 7
        assert len(g.source_nodes) == 3
        assert len(g.root_nodes) == 1
