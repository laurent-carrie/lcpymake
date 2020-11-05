from pathlib import Path
# pylint:disable=E0401
import pytest
# pylint:enable=E0401
from lcpymake import api


def dummy():
    def info(sources, targets):
        info = f'build target {targets} from sources {sources}'
        return info

    def run(sources, targets):
        print(sources)
        print(targets)

    return api.Rule(info=info, run=run)


dummy_rule = dummy()


# pylint:disable=R0201


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

        j1 = [{'artefacts': ['foo.cpp'], 'scanned_deps': [], 'status': 'SOURCE_MISSING'},
              {'artefacts': ['bar.cpp'], 'scanned_deps': [], 'status': 'SOURCE_PRESENT'},
              {'artefacts': ['main.cpp'], 'scanned_deps': [],
                  'status': 'SOURCE_MISSING'},
              {'artefacts': ['foo.o'],
               'rule': "build target ['foo.o'] from sources ['foo.cpp']",
               'sources': ['foo.cpp'],
               'status': 'BUILT_PRESENT'},
              {'artefacts': ['bar.o'],
               'rule': "build target ['bar.o'] from sources ['bar.cpp']",
               'sources': ['bar.cpp'],
               'status': 'BUILT_MISSING'},
              {'artefacts': ['main.o'],
               'rule': "build target ['main.o'] from sources ['main.cpp']",
               'sources': ['main.cpp'],
               'status': 'BUILT_MISSING'},
              {'artefacts': ['hello'],
               'rule': "build target ['hello'] from sources ['main.o', 'bar.o', 'foo.o']",
               'sources': ['main.o', 'bar.o', 'foo.o'],
               'status': 'BUILT_MISSING'}]
        assert api.to_json(g) == j1

        with pytest.raises(api.ArtefactSeenSeveralTimes):
            api.create_source_node(g, 'main.cpp', scan=None)
        assert api.to_json(g) == j1

        with pytest.raises(api.NoSuchNode):
            api.create_built_node(g, artefacts=['blah'], sources=[
                'missing.cpp'], rule=dummy_rule)
        assert api.to_json(g) == j1
        print()
        print()
        api.gprint(g)
