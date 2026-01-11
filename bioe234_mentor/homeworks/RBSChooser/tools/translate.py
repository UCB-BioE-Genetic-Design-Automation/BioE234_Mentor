"""DNA translation helper.

Implements a simple DNA->protein translation using the standard genetic code.
Stops at the first stop codon. Raises errors for invalid input.

This module provides:
- Translate: a function-as-object with initiate()/run()
- translate(cds): a convenience wrapper that uses a cached instance
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Translate:
    """Translate a DNA coding sequence (CDS) into amino acids.

    Uses the standard genetic code. Translation halts at the first stop codon.

    Attributes:
        codon_table (dict): Maps each DNA codon (3-mer) to its amino acid
            single-letter code, using the string "Stop" for stop codons.
    """

    codon_table: Optional[dict] = None

    def initiate(self) -> None:
        """Initialize the codon table (standard genetic code)."""
        self.codon_table = {
            "TTT": "F",
            "TTC": "F",
            "TTA": "L",
            "TTG": "L",
            "CTT": "L",
            "CTC": "L",
            "CTA": "L",
            "CTG": "L",
            "ATT": "I",
            "ATC": "I",
            "ATA": "I",
            "ATG": "M",
            "GTT": "V",
            "GTC": "V",
            "GTA": "V",
            "GTG": "V",
            "TCT": "S",
            "TCC": "S",
            "TCA": "S",
            "TCG": "S",
            "CCT": "P",
            "CCC": "P",
            "CCA": "P",
            "CCG": "P",
            "ACT": "T",
            "ACC": "T",
            "ACA": "T",
            "ACG": "T",
            "GCT": "A",
            "GCC": "A",
            "GCA": "A",
            "GCG": "A",
            "TAT": "Y",
            "TAC": "Y",
            "TAA": "Stop",
            "TAG": "Stop",
            "CAT": "H",
            "CAC": "H",
            "CAA": "Q",
            "CAG": "Q",
            "AAT": "N",
            "AAC": "N",
            "AAA": "K",
            "AAG": "K",
            "GAT": "D",
            "GAC": "D",
            "GAA": "E",
            "GAG": "E",
            "TGT": "C",
            "TGC": "C",
            "TGA": "Stop",
            "TGG": "W",
            "CGT": "R",
            "CGC": "R",
            "CGA": "R",
            "CGG": "R",
            "AGT": "S",
            "AGC": "S",
            "AGA": "R",
            "AGG": "R",
            "GGT": "G",
            "GGC": "G",
            "GGA": "G",
            "GGG": "G",
        }

    def run(self, dna_sequence: str) -> str:
        """Translate a DNA sequence into a protein sequence.

        Parameters:
            dna_sequence (str): The DNA sequence to translate.

        Returns:
            str: The corresponding amino acid sequence.

        Raises:
            ValueError: If the DNA sequence length is not a multiple of three,
            contains untranslated sequence after a stop codon, contains invalid
            codons, or if initiate() was not called.
        """
        if self.codon_table is None:
            raise ValueError("Translate.initiate() must be called before run().")

        dna_sequence = dna_sequence.upper()

        if len(dna_sequence) % 3 != 0:
            raise ValueError("The DNA sequence length must be a multiple of 3.")

        protein = []
        for i in range(0, len(dna_sequence), 3):
            codon = dna_sequence[i : i + 3]
            if codon not in self.codon_table:
                raise ValueError(f"Invalid codon '{codon}' encountered in DNA sequence.")
            amino_acid = self.codon_table[codon]
            if amino_acid == "Stop":
                if i + 3 != len(dna_sequence):
                    raise ValueError("Untranslated sequence after stop codon.")
                break
            protein.append(amino_acid)

        return "".join(protein)


_TRANSLATOR: Optional[Translate] = None


def translate(cds: str) -> str:
    """Convenience wrapper for translating a CDS using a cached Translate instance."""
    global _TRANSLATOR
    if _TRANSLATOR is None:
        _TRANSLATOR = Translate()
        _TRANSLATOR.initiate()
    return _TRANSLATOR.run(cds)


def _main() -> None:
    # Example usage:
    protein_sequence = translate("ATGCGACGTTAA")
    print("Protein sequence:", protein_sequence)


if __name__ == "__main__":
    _main()
