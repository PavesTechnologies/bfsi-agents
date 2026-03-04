# domain/normalization/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseNormalizer(ABC):
    """
    Base contract for all document normalizers.
    Input  : validated + extracted data (dict)
    Output : canonical / normalized data (dict)
    """

    @abstractmethod
    def normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize extracted document data into canonical form.
        Must be implemented by each document normalizer.
        """
        pass
