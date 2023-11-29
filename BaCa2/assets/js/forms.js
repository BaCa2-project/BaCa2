function toggleField(field, on) {
    if (on)
        $(field).attr('disabled', false);
    else {
        field.val('');
        if (field.hasClass('is-invalid')) {
            field.closest('.input-block').find('.invalid-feedback').remove();
            field.removeClass('is-invalid');
        }
        field.removeClass('is-valid')
        $(field).attr('disabled', true);
    }
}

function toggleFieldGroup(formElementGroup, on) {
    formElementGroup.find('input').each(function () {
        toggleField($(this), on)
    });
}

function formsSetup() {
    groupToggleBtnSetup();
    toggleableFieldSetup();
}

function toggleableFieldSetup() {
    const buttons = $('.field-toggle-btn');

    buttons.on('click', function(e) {
        let on = false;
        e.preventDefault();
        toggleTextSwitchBtn($(this));

        if ($(this).hasClass('switch-on'))
            on = true;

        toggleField($(this).closest('.input-group').find('input'), on);
    });

    buttons.each(function () {
        let on = false;
        if ($(this).hasClass('switch-on'))
            on = true;
        toggleField($(this).closest('.input-group').find('input'), on);
    });
}

function groupToggleBtnSetup() {
    const buttons = $('.group-toggle-btn');

    buttons.on('click', function(e) {
        let on = false;
        e.preventDefault();
        toggleTextSwitchBtn($(this));

        if ($(this).hasClass('switch-on'))
            on = true;

        toggleFieldGroup($(this).closest('.form-element-group'), on)
    });

    buttons.each(function () {
        let on  = false;
        if ($(this).hasClass('switch-on'))
            on = true;
        toggleFieldGroup($(this).closest('.form-element-group'), on)
    });
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