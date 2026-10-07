import unittest

from app.services.document_comparison import compare_documents
from app.services.document_extractors.base import (
    DocumentSection,
    ExtractedDocument,
)


class CompareDocumentsTests(unittest.TestCase):
    def test_returns_overall_similarity_when_sections_match(self) -> None:
        original = ExtractedDocument(
            filename="original.pdf",
            file_type="pdf",
            mime_type="application/pdf",
            size_bytes=100,
            text="A matching document section.",
            structure=[{"type": "heading"}],
            sections=[
                DocumentSection(
                    type="heading",
                    identifier="original-heading",
                    text="A matching document section.",
                )
            ],
        )
        comparison = ExtractedDocument(
            filename="comparison.pdf",
            file_type="pdf",
            mime_type="application/pdf",
            size_bytes=100,
            text="A matching document section.",
            structure=[{"type": "heading"}],
            sections=[
                DocumentSection(
                    type="heading",
                    identifier="comparison-heading",
                    text="A matching document section.",
                )
            ],
        )

        result = compare_documents(original, comparison)

        self.assertEqual(result["overall_similarity"], 100.0)
        self.assertEqual(len(result["matching_sections"]), 1)


if __name__ == "__main__":
    unittest.main()
