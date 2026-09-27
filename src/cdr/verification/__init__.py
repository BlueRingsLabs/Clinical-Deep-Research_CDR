"""
CDR Verification Layer

Citation verification and entailment checking.
"""

from cdr.verification.verifier import (
    BatchVerificationResult,
    CitationChecker,
    CitationCheckResult,
    Verifier,
    batch_verify,
)

__all__ = [
    "Verifier",
    "CitationChecker",
    "CitationCheckResult",
    "batch_verify",
    "BatchVerificationResult",
]
