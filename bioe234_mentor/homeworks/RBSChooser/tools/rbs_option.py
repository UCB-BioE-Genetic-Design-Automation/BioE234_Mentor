from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RBSOption:
    """
    Candidate option harvested from a native gene.

    - utr: 5' UTR sequence on the coding strand
    - cds: CDS sequence on the coding strand
    - gene_name: human readable identifier (gene or locus_tag)
    - first_six_aas: cached translate(cds)[:6]
    """
    utr: str
    cds: str
    gene_name: str
    first_six_aas: str