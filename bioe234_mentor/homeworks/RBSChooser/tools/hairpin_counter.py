

"""Hairpin counter utility.

Counts simple exact-match stem-loop-stem hairpin patterns in a DNA sequence.

Note: This is a simplified heuristic. It does not model thermodynamic stability.
"""

from __future__ import annotations


def hairpin_counter(sequence: str, min_stem: int = 3, min_loop: int = 4, max_loop: int = 9) -> int:
    """Count potential hairpin structures in a DNA sequence.

    Hairpins are common secondary structures in nucleic acids where a sequence
    of nucleotides can fold back on itself to form a double-stranded stem with a
    single-stranded loop.

    The algorithm searches for regions within the sequence where a segment can
    base-pair with its reverse complement separated by a loop. This function
    scans for such occurrences by examining every possible substring as a
    potential stem and ensuring the intervening sequence (the loop) meets the
    specified length requirements.

    Parameters:
        sequence (str): The DNA sequence to analyze.
        min_stem (int): Minimum number of bases in the stem for stable hairpin.
                        The stem must be able to form at least this many
                        complementary base pairs to be considered.
        min_loop (int): Minimum number of bases in the loop. This prevents the
                        formation of overly tight hairpins which may not be
                        biologically relevant.
        max_loop (int): Maximum number of bases in the loop. This constrains the
                        loop to a realistic size, preventing unlikely
                        structures.

    Returns:
        int: The count of potential hairpin structures detected, indicating
        regions where secondary structure formation might inhibit biological
        processes like transcription or translation.

    This method does not account for the thermodynamic stability of the
    predicted hairpins, focusing solely on their potential for formation based
    on sequence complementarity and specified geometrical constraints.
    """
    count = 0
    seq_len = len(sequence)

    # Iterate through each base to consider it as a start of a stem
    for i in range(seq_len):
        # Only consider end points that would fit within the loop constraints
        for j in range(i + min_stem + min_loop, min(i + min_stem + max_loop + 1, seq_len)):
            stem1 = sequence[i : i + min_stem]
            stem2 = sequence[j : j + min_stem]

            # Check if the stems are complementary (reverse complement match)
            stem2_rc = "".join(["ATCG"["TAGC".index(n)] for n in stem2[::-1]])

            if stem1 == stem2_rc:
                count += 1

    return count


def _main() -> None:
    # Example usage
    # sequence = "GGCTAATTTAGCCATTAAGGCTAATAGGCTAA"
    count = hairpin_counter("AAAAAAAAAAAAAAAAAAAAAAAAAAA")
    print("Zero hairpins:", count)

    count = hairpin_counter("AAAAACCCAAAAAAAAAAGGGAAAAAA")
    print("CCC-N10-GGG:", count)

    count = hairpin_counter("AAAAACCCAAAAAAAAAGGGAAAAAA")
    print("CCC-N9-GGG:", count)

    count = hairpin_counter("AAAAACCCCAAAAAAAAGGGGAAAAAA")
    print("CCCC-N8-GGGG:", count)

    count = hairpin_counter("AAAAACACGAAAAAAAACGTGAAAAAA")
    print("CACG-N8-CGTG:", count)

    count = hairpin_counter("AAAACCCCCAAAAAAAAGGGGGAAA")
    print("CCCCC-N8-GGGGG:", count)

    count = hairpin_counter("AAAACCCCCAAAAAAAGGGGGAAA")
    print("CCCCC-N7-GGGGG:", count)


if __name__ == "__main__":
    _main()