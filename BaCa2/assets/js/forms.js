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
    toggleableGroupSetup();
    toggleableFieldSetup();
    confirmationPopupSetup();
    liveValidationSetup();
}

function liveValidationSetup() {
    $('form').each(function () {
        submitButtonRefresh($(this));
    });
}

function submitButtonRefresh(form) {
    if (form.find('.live-validation').filter(function () {
        return ($(this)).find('input:not(:disabled):not(.is-valid)').length > 0;
    }).length > 0)
        form.find('.submit-btn').attr('disabled', true);
    else
        form.find('.submit-btn').attr('disabled', false);
}

function toggleableFieldSetup() {
    const buttons = $('.field-toggle-btn');

    buttons.on('click', function(e) {
        e.preventDefault();
        toggleTextSwitchBtn($(this));
        let on = false;
        const input = $(this).closest('.input-group').find('input')

        if ($(this).hasClass('switch-on'))
            on = true;

        toggleField(input, on);

        if (on)
            input.focus();

        submitButtonRefresh($(this).closest('form'));
    });

    buttons.each(function () {
        let on = false;
        if ($(this).hasClass('switch-on'))
            on = true;
        toggleField($(this).closest('.input-group').find('input'), on);
    });
}

function toggleableGroupSetup() {
    const buttons = $('.group-toggle-btn');

    buttons.on('click', function(e) {
        e.preventDefault();
        toggleTextSwitchBtn($(this));
        let on = false;
        const group = $(this).closest('.form-element-group');

        if ($(this).hasClass('switch-on'))
            on = true;

        toggleFieldGroup(group, on)

        if (on)
            group.find('input:first').focus()

        submitButtonRefresh($(this).closest('form'));
    });

    buttons.each(function () {
        let on  = false;
        if ($(this).hasClass('switch-on'))
            on = true;
        toggleFieldGroup($(this).closest('.form-element-group'), on)
    });
}

function confirmationPopupSetup() {
    $('.submit-btn').filter(function () {
        return $(this).data('bs-toggle') === 'modal';
    }).filter(function () {
        return $($(this).data('bs-target')).find('.input-summary').length > 0;
    }).on('click', function (e) {
        e.preventDefault();
        const popup = $($(this).data('bs-target'));

        popup.find('.input-summary-label').text(function () {
            return $('#' + $(this).data('input-target')).closest('.input-group')
                .find('label').text() + ':';
        });

        popup.find('.input-summary-value').text(function () {
            const value = $('#' + $(this).data('input-target')).val();
            return value.length > 0 ? value : '-';
        });
    });

    $('.form-confirmation-popup .submit-btn').on('click', function () {
        $(this).closest('.form-confirmation-popup').modal('hide');
        $('#' + $(this).data('form-target')).submit();
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

                submitButtonRefresh($(field).closest('form'));
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

                $(field).closest('form').find('.submit-btn').attr('disabled', true);
            }
        }
    });
}