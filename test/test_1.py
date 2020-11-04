from lcpymake import api
from pathlib import Path
import pytest
from typing import List
import subprocess
import string


def dummy_rule(sources, target):
    pass


class Test_1:

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

        j1 = {'0': {'artefacts': ['foo.cpp'], 'id': 0},
              '1': {'artefacts': ['bar.cpp'], 'id': 1},
              '2': {'artefacts': ['main.cpp'], 'id': 2},
              '3': {'artefacts': ['foo.o'], 'id': 3},
              '4': {'artefacts': ['bar.o'], 'id': 4},
              '5': {'artefacts': ['main.o'], 'id': 5},
              '6': {'artefacts': ['hello'], 'id': 6}}
        assert api.to_json(g) == j1

        with pytest.raises(api.ArtefactSeenSeveralTimes):
            api.create_source_node(g, 'main.cpp')
        assert api.to_json(g) == j1

        j2 = {'0': {'artefacts': ['foo.cpp'], 'id': 0},
              '1': {'artefacts': ['bar.cpp'], 'id': 1},
              '2': {'artefacts': ['main.cpp'], 'id': 2},
              '3': {'artefacts': ['foo.o'], 'id': 3},
              '4': {'artefacts': ['bar.o'], 'id': 4},
              '5': {'artefacts': ['main.o'], 'id': 5},
              '6': {'artefacts': ['hello'], 'id': 6}}
        assert api.to_json(g) == j2
