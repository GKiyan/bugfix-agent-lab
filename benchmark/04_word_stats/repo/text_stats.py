from tokenizer import tokenize


def word_count(text):
    """Number of words in `text`."""
    return len(tokenize(text))


def most_common_word(text):
    """The most frequent word in `text` (ties: the first one seen)."""
    counts = {}
    for word in tokenize(text):
        counts[word] = counts.get(word, 0) + 1
    return max(counts, key=counts.get)
