from typing import Dict

from widgets.forms import BaCa2ModelForm


class CreateUserForm(BaCa2ModelForm):
    @classmethod
    def handle_valid_request(cls, request) -> Dict[str, str]:
        pass

    @classmethod
    def handle_invalid_request(cls, request, errors: dict) -> Dict[str, str]:
        pass

    @classmethod
    def handle_impermissible_request(cls, request) -> Dict[str, str]:
        pass

    @classmethod
    def handle_error(cls, request, error: Exception) -> Dict[str, str]:
        pass