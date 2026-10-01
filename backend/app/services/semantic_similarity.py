from __future__ import annotations

from dataclasses import dataclass

@dataclass

class SemanticSimilarityResult:

    score: float

    status: str

class SemanticSimilarityEngine:

    """

    Semantic similarity engine interface.

    This layer is intentionally provider-independent.

    A private/local vision-language model can be connected

    later without changing the API contract.

    """

    def analyze(

        self,

        original_image: bytes,

        comparison_image: bytes,

    ) -> SemanticSimilarityResult:

        # Semantic model integration point.

        #

        # Future implementations may use:

        #

        # - Local vision-language model

        # - Private inference server

        # - Enterprise GPU inference

        #

        # No external data transmission happens here.

        return SemanticSimilarityResult(

            score=0.0,

            status="semantic_engine_pending",

        )