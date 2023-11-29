$(document).ready(function() {
    $('.toggleable-off').each(function() {
        const toggleable = $(this);
        const input = toggleable.find('input');
        input.attr('disabled', true);
    });
});

function toggleField(fieldName, buttonTextOff, buttonTextOn) {
    const field = document.getElementById(fieldName);
    const toggleable = field.closest('.toggleable');
    const button = $(toggleable).find('button');
    field.value = '';

    if (toggleable.classList.contains('toggleable-off')) {
        toggleable.classList.remove('toggleable-off');
        toggleable.classList.add('toggleable-on');
        $(field).attr('disabled', false);
        button.text(buttonTextOn);
    } else {
        if (field.classList.contains('is-invalid')) {
            field.classList.remove('is-invalid');
            const errors = $(field.closest('.input-block')).find('.invalid-feedback');
            errors.remove();
        } else if (field.classList.contains('is-valid')) {
            field.classList.remove('is-valid');
        }
        toggleable.classList.remove('toggleable-on');
        toggleable.classList.add('toggleable-off');
        $(field).attr('disabled', true);
        button.text(buttonTextOff);
    }
}

function formsSetup() {
    groupToggleBtnSetup();
}

function groupToggleBtnSetup() {
    const buttons = $('.group-toggle-btn');

    buttons.on('click', function(e) {
        e.preventDefault();
        toggleTextSwitchBtn($(this));
        updateToggleableGroup($(this));
    });

    buttons.each(function () {
        updateToggleableGroup($(this));
    });
}

function updateToggleableGroup(btn) {
    const fields = btn.closest('.form-element-group').find('input');

    if (btn.hasClass('switch-on'))
        fields.attr('disabled', false);
    else
        fields.attr('disabled', true);
}

function update_validation_status(field, fieldCls, required, minLength, url) {
    const value = $(field).val();
    $.ajax({
        url: url,
        data: {
            'field_cls': fieldCls,
            'value': value,
            'required': required,
            'min_length': minLength,
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
                    $(input_block).append(
                        "<div class='invalid-feedback'>" + data.messages[i] + "</div>"
                    );
                }
            }
        }
    });
}