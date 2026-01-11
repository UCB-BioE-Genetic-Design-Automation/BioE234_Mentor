"""Edit distance utility.

Implements Levenshtein edit distance (global alignment).

Levenshtein distance is the minimum number of single-character edits
(insertions, deletions, substitutions) required to transform one string into
another.
"""

from __future__ import annotations


def edit_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein edit distance (global) between two strings.

    Parameters:
        s1 (str): The first string to compare.
        s2 (str): The second string to compare.

    Returns:
        int: The Levenshtein edit distance, defined as the minimum number of edits
        (insertions, deletions, substitutions) required to transform one string into the other.
    """
    s1_len = len(s1)
    s2_len = len(s2)
    dist = [[0] * (s2_len + 1) for _ in range(s1_len + 1)]

    # Initialize distances for transformations involving empty strings
    for i in range(s1_len + 1):
        dist[i][0] = i
    for j in range(s2_len + 1):
        dist[0][j] = j

    # Compute distances
    for i in range(1, s1_len + 1):
        for j in range(1, s2_len + 1):
            if s1[i - 1] == s2[j - 1]:
                dist[i][j] = dist[i - 1][j - 1]
            else:
                dist[i][j] = 1 + min(dist[i - 1][j], dist[i][j - 1], dist[i - 1][j - 1])

    return dist[s1_len][s2_len]


def _main() -> None:
    # Example usage
    distance1 = edit_distance("AACAAGATAT", "AACATGATAT")
    print("Edit distance 1:", distance1)

    distance2 = edit_distance("AACAAGTTAT", "ATCAAGTTCT")
    print("Edit distance 2:", distance2)


if __name__ == "__main__":
    _main()
