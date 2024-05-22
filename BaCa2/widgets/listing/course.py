from core.choices import (
    INTERNAL_ERROR_STATUSES,
    JUDGING_ERROR_STATUSES,
    OK_FINAL_STATUSES,
    PENDING_STATUSES,
    SOURCE_ERROR_STATUSES
)
from widgets.listing import RowStylingRule


def get_status_rules():
    return [
        OKSubmitRule(),
        PendingSubmitRule(),
        JudgingErrorSubmitRule(),
        SourceErrorSubmitRule(),
        InternalErrorSubmitRule()
    ]


class OKSubmitRule(RowStylingRule):
    def __init__(self):
        super().__init__(
            strict=False,
            mappings={'_submit_status': list(map(str, OK_FINAL_STATUSES)),
                      'status': list(map(str, OK_FINAL_STATUSES))},
            row_class='ok-submit-row'
        )


class PendingSubmitRule(RowStylingRule):
    def __init__(self):
        super().__init__(
            strict=False,
            mappings={'_submit_status': list(map(str, PENDING_STATUSES)),
                      'status': list(map(str, PENDING_STATUSES))},
            row_class='pending-submit-row'
        )


class JudgingErrorSubmitRule(RowStylingRule):
    def __init__(self):
        super().__init__(
            strict=False,
            mappings={'_submit_status': list(map(str, JUDGING_ERROR_STATUSES)),
                      'status': list(map(str, JUDGING_ERROR_STATUSES))},
            row_class='judging-error-submit-row'
        )


class SourceErrorSubmitRule(RowStylingRule):
    def __init__(self):
        super().__init__(
            strict=False,
            mappings={'_submit_status': list(map(str, SOURCE_ERROR_STATUSES)),
                      'status': list(map(str, SOURCE_ERROR_STATUSES))},
            row_class='source-error-submit-row'
        )


class InternalErrorSubmitRule(RowStylingRule):
    def __init__(self):
        super().__init__(
            strict=False,
            mappings={'_submit_status': list(map(str, INTERNAL_ERROR_STATUSES)),
                      'status': list(map(str, INTERNAL_ERROR_STATUSES))},
            row_class='internal-error-submit-row'
        )
