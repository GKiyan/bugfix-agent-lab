import pytest

from grades import letter_grade


@pytest.mark.parametrize(
    "score, expected",
    [(100, "A"), (95, "A"), (85, "B"), (75, "C"), (65, "D"), (30, "F"), (0, "F")],
)
def test_typical_scores(score, expected):
    assert letter_grade(score) == expected


@pytest.mark.parametrize(
    "score, expected",
    [(90, "A"), (89, "B"), (80, "B"), (79, "C"), (70, "C"), (69, "D"), (60, "D"), (59, "F")],
)
def test_boundaries(score, expected):
    assert letter_grade(score) == expected


def test_invalid_score():
    with pytest.raises(ValueError):
        letter_grade(101)
