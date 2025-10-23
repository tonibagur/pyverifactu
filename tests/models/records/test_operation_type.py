"""Tests for OperationType enum"""

from verifactu.models.records import OperationType


class TestOperationType:
    """Test OperationType enum helper methods"""

    def test_has_working_helpers(self) -> None:
        """Test enum classification helper methods"""

        # Test SUBJECT
        assert OperationType.SUBJECT.is_subject()
        assert not OperationType.SUBJECT.is_non_subject()
        assert not OperationType.SUBJECT.is_exempt()

        # Test NON_SUBJECT
        assert not OperationType.NON_SUBJECT.is_subject()
        assert OperationType.NON_SUBJECT.is_non_subject()
        assert not OperationType.NON_SUBJECT.is_exempt()

        # Test EXEMPT_BY_ARTICLE_21
        assert not OperationType.EXEMPT_BY_ARTICLE_21.is_subject()
        assert not OperationType.EXEMPT_BY_ARTICLE_21.is_non_subject()
        assert OperationType.EXEMPT_BY_ARTICLE_21.is_exempt()
