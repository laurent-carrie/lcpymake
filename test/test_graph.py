from lcpymake import api
from pathlib import Path
import pytest
from typing import List
import subprocess
import string


def info(sources, targets):
    info = f'build target {targets} from sources {sources}'
    return info


def run(sources, targets):
    pass


dummy_rule = api.Rule(info, run)


class Test_graph:

    def test_graph(self, datadir):
        g = api.create()
        api.create_source_node(g, 'foo.cpp')
        api.create_source_node(g, 'bar.cpp')
        api.create_source_node(g, 'main.cpp')
        api.create_built_node(g, artefacts=['foo.o'], sources=[
            'foo.cpp'], rule=dummy_rule)
        api.create_built_node(g, artefacts=['bar.o'], sources=[
            'bar.cpp'], rule=dummy_rule)
        api.create_built_node(g, artefacts=['main.o'], sources=[
            'main.cpp'], rule=dummy_rule)
        api.create_built_node(g, artefacts=['hello'], sources=[
            'main.o', 'bar.o', 'foo.o'], rule=dummy_rule)

        j1 = [{'artefacts': ['foo.cpp']},
              {'artefacts': ['bar.cpp']},
              {'artefacts': ['main.cpp']},
              {'artefacts': ['foo.o'],
               'rule': "build target ['foo.o'] from sources ['foo.cpp']",
               'sources': ['foo.cpp']},
              {'artefacts': ['bar.o'],
               'rule': "build target ['bar.o'] from sources ['bar.cpp']",
               'sources': ['bar.cpp']},
              {'artefacts': ['main.o'],
               'rule': "build target ['main.o'] from sources ['main.cpp']",
               'sources': ['main.cpp']},
              {'artefacts': ['hello'],
               'rule': "build target ['hello'] from sources ['main.o', 'bar.o', 'foo.o']",
               'sources': ['main.o', 'bar.o', 'foo.o']}]
        assert api.to_json(g) == j1

        with pytest.raises(api.ArtefactSeenSeveralTimes):
            api.create_source_node(g, 'main.cpp')
        assert api.to_json(g) == j1

        with pytest.raises(api.NoSuchNode):
            api.create_built_node(g, artefacts=['blah'], sources=[
                'missing.cpp'], rule=dummy_rule)
        assert api.to_json(g) == j1
