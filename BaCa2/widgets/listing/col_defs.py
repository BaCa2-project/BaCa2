from widgets.forms.course import RejudgeSubmitFormWidget
from widgets.listing.columns import FormSubmitColumn


class RejudgeSubmitColumn(FormSubmitColumn):
    def __init__(self, course_id, request):
        super().__init__(name='rejudge',
                         form_widget=RejudgeSubmitFormWidget(course_id=course_id, request=request),
                         mappings={'submit_id': 'id'},
                         btn_icon='exclamation-triangle',
                         header_icon='clock-history',
                         condition_key='is_legacy',
                         condition_value='true',
                         disabled_appearance=FormSubmitColumn.DisabledAppearance.ICON,
                         disabled_content='check-lg')
