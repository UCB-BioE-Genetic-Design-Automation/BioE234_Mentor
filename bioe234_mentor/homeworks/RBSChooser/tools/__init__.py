"""RBSChooser helper tools.

This package re-exports the specific helper functions the student notebook
expects to access via imports (or via Mentor wiring):
- translate
- edit_distance
- hairpin_counter

It also exports a couple of optional convenience symbols:
- Translate (class)
- calculate_edit_distance (function)
"""

from .translate import Translate, translate
from .edit_distance import calculate_edit_distance, edit_distance
from .hairpin_counter import hairpin_counter

__all__ = [
    "translate",
    "edit_distance",
    "hairpin_counter",
    # optional extras
    "Translate",
    "calculate_edit_distance",
]