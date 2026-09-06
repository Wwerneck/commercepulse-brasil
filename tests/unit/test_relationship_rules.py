import pandas as pd

from src.quality.rules import accepted_values, false_flag, relationship_exists, unique_key


def test_unique_key_flags_duplicate_rows() -> None:
    result = unique_key(pd.DataFrame({"id": [1, 1, 2]}), ["id"])

    assert not result.passed
    assert result.failed_count == 2


def test_relationship_exists_flags_orphans() -> None:
    child = pd.DataFrame({"parent_id": [1, 2, 3]})
    parent = pd.DataFrame({"id": [1, 2]})

    result = relationship_exists(child, "parent_id", parent, "id", "child_parent")

    assert not result.passed
    assert result.failed_count == 1


def test_accepted_values_flags_unexpected_value() -> None:
    result = accepted_values(pd.DataFrame({"status": ["ok", "bad"]}), "status", {"ok"})

    assert not result.passed
    assert result.failed_count == 1


def test_false_flag_counts_true_flags() -> None:
    result = false_flag(pd.DataFrame({"has_error": [False, True, False]}), "has_error")

    assert not result.passed
    assert result.failed_count == 1
