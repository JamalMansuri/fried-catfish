"""Catfish — stress-test plans in a tournament, decide in one card.

Abstracts Google's AI Co-Scientist (arXiv:2502.18864) generate->debate->evolve
methodology into a portable decision engine for project-management and technical calls.

Honest limit: Catfish produces stress-tested *options*, not verified *answers*. A
Bradley-Terry score is relative persuasiveness among LLM judges, not truth. The human
gate is the validator.
"""

__version__ = "0.1.0"
