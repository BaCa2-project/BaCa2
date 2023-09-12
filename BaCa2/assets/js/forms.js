$(document).ready(function() {
    $('.toggleable-off').each(function() {
        const toggleable = $(this);
        const input = toggleable.find('input');
        input.attr('disabled', true);
    });
});

function toggleField(field_name, button_text_off, button_text_on) {
    console.log(field_name);
    const field = document.getElementById(field_name);
    const toggleable = field.closest('.toggleable');
    const button = $(toggleable).find('button');
    field.value = '';

    if (toggleable.classList.contains('toggleable-off')) {
        toggleable.classList.remove('toggleable-off');
        toggleable.classList.add('toggleable-on');
        $(field).attr('disabled', false);
        button.text(button_text_on);
    } else {
        if (field.classList.contains('is-invalid')) {
            field.classList.remove('is-invalid');
            const errors = $(field.closest('.input-block')).find('.invalid-feedback');
            console.log(errors);
            errors.remove();
        }
        toggleable.classList.remove('toggleable-on');
        toggleable.classList.add('toggleable-off');
        $(field).attr('disabled', true);
        button.text(button_text_off);
    }
}

function update_validation_status(field, field_cls, required, min_length, url) {
    const value = $(field).val();
    $.ajax({
        url: url,
        data: {
            'field_cls': field_cls,
            'value': value,
            'required': required,
            'min_length': min_length,
        },
        dataType: 'json',
        success: function (data) {
            if (data.status === 'ok') {
                $(field).removeClass('is-invalid');
                $(field).addClass('is-valid');
                const input_block = $(field).closest('.input-block');
                $(input_block).find('.invalid-feedback').remove();
            } else {
                $(field).removeClass('is-valid');
                $(field).addClass('is-invalid');
                const input_block = $(field).closest('.input-block');
                $(input_block).find('.invalid-feedback').remove();
                for (let i = 0; i < data.messages.length; i++) {
                    $(input_block).append("<div class='invalid-feedback'>" + data.messages[i] + "</div>");
                }
            }
        }
    });
}