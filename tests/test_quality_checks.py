
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.insurance_pipeline.quality_checks import (
    run_quality_checks,
)


def test_quality_checks_fail_on_missing_rows():
    client = MagicMock()

    fake_result = SimpleNamespace(
        raw_count=5000,
        clean_count=4990,
        rejected_count=6,
        duplicate_clean_ids=0,
    )

    client.query.return_value.result.return_value = [
        fake_result
    ]

    with pytest.raises(ValueError, match="Clean count mismatch"):
        run_quality_checks(
            client=client,
            project_id="test-project",
            location="europe-west9",
            expected_raw=5000,
            expected_clean=4994,
            expected_rejected=6,
        )
