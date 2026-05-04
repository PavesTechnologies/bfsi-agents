from .utils import normalize_name


class VoterIDNormalizer:
    def normalize(self, ocr_result: dict) -> dict:
        """
        Map validate_voter_id_ocr output to the internal cross-validation schema.
        """
        return {
            "document_type": "voter_id",
            "epic_number": ocr_result.get("epic_number"),
            "full_name": normalize_name(ocr_result.get("name")),
        }
