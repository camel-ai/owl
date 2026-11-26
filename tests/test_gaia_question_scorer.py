import pytest

from owl.utils.gaia import GAIABenchmark


@pytest.mark.parametrize("ground_truth", ["42", "Paris", "a, b"])
def test_question_scorer_missing_answer_is_incorrect(ground_truth):
    benchmark = object.__new__(GAIABenchmark)

    assert benchmark.question_scorer(None, ground_truth) is False
