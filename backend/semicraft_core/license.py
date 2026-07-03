"""Single-sourced license/disclaimer text for generated file headers.

Per IMPLEMENTATION_PLAN.md §1 and SemiCraft_PRD.md §15: every generated file
header stamps this disclaimer alongside tool name+version and config hash.
Header rendering (WP-02 `Header` node / render/style.py) imports this
constant rather than redefining the text.
"""

DISCLAIMER: str = (
    "Generated code is provided as-is, without warranty of any kind. "
    "Free for commercial and non-commercial use at the user's own risk."
)
