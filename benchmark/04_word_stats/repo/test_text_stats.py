from text_stats import most_common_word, word_count


def test_simple_sentence():
    assert word_count("the quick brown fox") == 4


def test_multiple_spaces():
    assert word_count("hello   world") == 2


def test_newlines_and_tabs():
    assert word_count("one\ntwo\tthree") == 3


def test_empty_text():
    assert word_count("") == 0


def test_most_common_word():
    assert most_common_word("The cat and the dog") == "the"


def test_most_common_word_with_extra_spaces():
    assert most_common_word("one  two  three  two") == "two"
