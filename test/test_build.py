from pathlib import Path
import pytest
from lcpymake import api
from lcpymake import rule
from lcpymake.basic_cpp_rules import scan_cpp, compile_rule, link_rule


def dummy():
    def info(sources, targets):
        info = f'build target {[str(t) for t in targets]} from sources {[str(s) for s in sources]}'
        return info

    def run(sources, targets):
        print(sources)
        print(targets)

    return rule.Rule(info=info, run=run)


dummy_rule = dummy()


class TestBuild:

    def test_build(self, datadir):
        srcdir = Path(datadir) / 'src'
        sandbox = Path(datadir) / 'sandbox'
        g = api.create(srcdir=srcdir, sandbox=sandbox)

        src_include_path = [srcdir / 'mylibs']
        include_path = [sandbox / 'mylibs']

        api.create_source_node(g, 'mylibs/foolib/foo.cpp',
                               scan=scan_cpp(src_include_path))
        api.create_source_node(g, 'mylibs/barlib/bar.cpp',
                               scan=scan_cpp(src_include_path))
        api.create_source_node(g, 'main.cpp', scan=scan_cpp(src_include_path))
        api.create_built_node(g, artefacts=['mylibs/foolib/foo.o'], sources=[
            'mylibs/foolib/foo.cpp'], rule=compile_rule(include_path))
        api.create_built_node(g, artefacts=['mylibs/barlib/bar.o'], sources=[
            'mylibs/barlib/bar.cpp'], rule=compile_rule(include_path))
        api.create_built_node(g, artefacts=['main.o'], sources=[
            'main.cpp'], rule=compile_rule(include_path))
        api.create_built_node(g, artefacts=['hello'], sources=[
            'main.o', 'mylibs/barlib/bar.o', 'mylibs/foolib/foo.o'], rule=link_rule())

        j = g.to_json()
        assert j["mylibs/barlib/bar.h"]["stored_digest"] is None
        assert str(g.first_candidate_for_build) == "mylibs/barlib/bar.h"

        g.build_one_step()
        j = g.to_json()
        assert j["mylibs/barlib/bar.h"]["stored_digest"] is not None

        g.build_one_step()
        assert str(g.first_candidate_for_build) == "mylibs/barlib/bar.o"

        g.build_one_step()
        assert str(g.first_candidate_for_build) == "mylibs/foolib/foo.h"

        g.build_one_step()
        # assert str(g.first_candidate_for_build) == "main.cpp"

        g.build_one_step()
        # assert str(g.first_candidate_for_build) == "main.o"

        g.build_one_step()
        # assert str(g.first_candidate_for_build) == "mylibs/foolib/foo.cpp"

        g.build_one_step()
        # assert str(g.first_candidate_for_build) == "mylibs/foolib/foo.o"

        g.build_one_step()
        assert str(g.first_candidate_for_build) == "hello"

        assert not (sandbox / "hello").exists()
        g.build_one_step()
        assert (sandbox / "hello").exists()
        assert g.first_candidate_for_build is None

        # remove one intermediary target, check that the whole tree is not rebuilt
        (sandbox / "mylibs/barlib/bar.o").unlink()
        g.touch()
        assert str(g.first_candidate_for_build) == "mylibs/barlib/bar.o"
        g.build_one_step()
        assert str(g.first_candidate_for_build) == "None"

        # change one file in a way that it does __not__ change the binary code
        data = """
// useless comment
#include <iostream>
#include "foolib/foo.h"
        int foo(int i) {
            return i * 3;
        }
"""
        (srcdir / "mylibs/foolib/foo.cpp").write_text(data)
        g.touch()
        assert str(g.first_candidate_for_build) == "mylibs/foolib/foo.o"
        g.build_one_step()
        # the build stops because the new version of foo.o has the same digest as the previous one
        assert str(g.first_candidate_for_build) == "None"

        # change one file in a way that it does change the binary code
        data = """
// useless comment
#include <iostream>
#include "foolib/foo.h"
        int foo(int i) {
            return i * 42;
        }
"""
        (srcdir / "mylibs/foolib/foo.cpp").write_text(data)
        g.touch()
        assert str(g.first_candidate_for_build) == "mylibs/foolib/foo.o"
        g.build_one_step()
        # the build does not stop because foo.o does not have the same binary code. linking hello is necessary
        assert str(g.first_candidate_for_build) == "hello"
