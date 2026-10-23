def letter_grade(score):
    """Convert a score out of 100 to a letter grade.

    A: 90 and above, B: 80 to 89, C: 70 to 79, D: 60 to 69, F: below 60.
    """
    if score < 0 or score > 100:
        raise ValueError(f"score must be between 0 and 100, got {score}")
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    return "F"
