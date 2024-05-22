from widgets.listing import RowStylingRule
from widgets import colors
from core.choices import ResultStatus


def get_submit_rules():
    return [
        SuccessfulSubmitRule(),
        FailedSubmitRule()
    ]


class SuccessfulSubmitRule(RowStylingRule):
    def __init__(self):
        super().__init__(
            mappings={'_submit_status': str(ResultStatus.OK)},
            row_class='success-submit-row'
        )


class FailedSubmitRule(RowStylingRule):
    def __init__(self):
        super().__init__(
            mappings={'_submit_status': [str(ResultStatus.ANS),
                                         str(ResultStatus.TLE),
                                         str(ResultStatus.RTE),
                                         str(ResultStatus.MEM),
                                         str(ResultStatus.CME),
                                         str(ResultStatus.RUL),
                                         str(ResultStatus.EXT),
                                         str(ResultStatus.ITL),
                                         str(ResultStatus.INT)]},
            row_class='failure-submit-row'
        )
