from visgen.preflight import branch_guard_message


def test_blocks_master_as_submodule():
    msg = branch_guard_message(True, "master")
    assert msg and "dedicated project branch" in msg


def test_blocks_main_as_submodule():
    assert branch_guard_message(True, "main") is not None


def test_allows_project_branch_as_submodule():
    assert branch_guard_message(True, "visemi-catcanh") is None


def test_allows_master_when_standalone():
    assert branch_guard_message(False, "master") is None
