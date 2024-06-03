from django.utils.translation import gettext_lazy as _

from core.choices import (
    INTERNAL_ERROR_STATUSES,
    JUDGING_ERROR_STATUSES,
    OK_FINAL_STATUSES,
    PENDING_STATUSES,
    SOURCE_ERROR_STATUSES
)
from main.models import Course, User
from widgets.listing import RowStylingRule, TableWidget
from widgets.listing.columns import TextColumn


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


class CourseOverviewTable(TableWidget):
    def __init__(self, course: Course, member: User) -> None:
        taks_number = course.get_tasks_number()
        cleared_tasks_number = course.get_member_cleared_tasks_number(member)
        cleared_tasks_percentage = cleared_tasks_number / taks_number * 100 if taks_number else 0
        member_submits_number = course.get_member_submits_number(member)
        total_points = course.get_total_points()
        member_points = course.get_member_points(member)
        points_percentage = member_points / total_points * 100 if total_points else 0

        course_overview = [
            {'title': _('Number of tasks'), 'value': f'{taks_number}'},
            {'title': _('Cleared tasks'), 'value': f'{cleared_tasks_number}'},
            {'title': _('Cleared tasks percentage'), 'value': f'{cleared_tasks_percentage:.2f}%'},
            {'title': _('Your submits'), 'value': f'{member_submits_number}'},
            {'title': _('Total points'), 'value': f'{total_points:.2f}'},
            {'title': _('Your points'), 'value': f'{member_points:.2f}'},
            {'title': _('Points percentage'), 'value': f'{points_percentage:.2f}%'}
        ]

        super().__init__(
            name='course_overview_table',
            title=f'{course.name} ' + _('overview'),
            data_source=course_overview,
            cols=[TextColumn(name='title', sortable=False),
                  TextColumn(name='value', sortable=False)],
            hide_col_headers=True,
            allow_global_search=False,
            default_sorting=False,
        )
