"""
CDR Synthesis Layer

Evidence synthesis and GRADE assessment.
"""

from cdr.synthesis.synthesizer import (
    EvidenceSynthesizer,
    SynthesisResult,
    assess_publication_bias,
    calculate_pooled_estimate,
)

__all__ = [
    "EvidenceSynthesizer",
    "SynthesisResult",
    "calculate_pooled_estimate",
    "assess_publication_bias",
]
