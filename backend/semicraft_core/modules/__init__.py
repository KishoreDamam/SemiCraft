"""Full RTL modules (Phase 2, Appendix A.3).

A *module* is a complete, reusable, parameterized RTL block (as opposed to a
snippet, which is a fragment). Each module is one file in this package exporting
a :class:`~.contract.ModuleDef` instance, discovered into the shared catalog by
:mod:`semicraft_core.snippets.registry` exactly like snippets. Modules add
multi-file output (rtl + doc, later tb), port-group metadata for documentation,
and a smoke-TB recipe (:class:`~.contract.TbSpec`).
"""
