// ---------------------------------------- forms setup --------------------------------------- //

function formsSetup() {
    ajaxPostSetup();
    toggleableGroupSetup();
    toggleableFieldSetup();
    confirmationPopupSetup();
    responsePopupsSetup();
    refreshButtonSetup();
    liveValidationSetup();
    tableSelectFieldSetup();
}

function ajaxPostSetup() {
    $('form').filter(function () {
        return $(this).attr("action") !== undefined;
    }).on('submit', function (e) {
        e.preventDefault();
        handleAjaxSubmit($(this));
    });
}

function refreshButtonSetup() {
    $('form').each(function () {
        const form = $(this)
        form.find('.form-refresh-button').on('click', function () {
           formRefresh(form)
        });
    });
}

function liveValidationSetup() {
    $('form').each(function () {
        submitButtonRefresh($(this));
    });
}

// --------------------------------------- toggle setup --------------------------------------- //

function toggleableFieldSetup() {
    const buttons = $('.field-toggle-btn');

    buttons.each(function () {
        toggleableFieldButtonInit($(this));
    });

    buttons.on('click', function(e) {
        toggleFieldButtonClickHandler(e, $(this))
    });
}

function toggleableFieldButtonInit(button) {
    let on = button.data('initial-state') !== 'off';
    if (button.hasClass('switch-on') && !on)
        toggleTextSwitchBtn(button)
    toggleField(button.closest('.input-group').find('input'), on);
}

function toggleableGroupSetup() {
    const buttons = $('.group-toggle-btn');

    buttons.each(function () {
        toggleableGroupButtonInit($(this))
    });

    buttons.on('click', function(e) {
        toggleGroupButtonClickHandler(e, $(this))
    });
}

function toggleableGroupButtonInit(button) {
    let on  = button.data('initial-state') !== 'off';
    if (button.hasClass('switch-on') && !on)
        toggleTextSwitchBtn(button)
    toggleFieldGroup(button.closest('.form-element-group'), on)
}

// ---------------------------------------- popup setup --------------------------------------- //

function confirmationPopupSetup() {
    $('.submit-btn').filter(function () {
        return $(this).data('bs-toggle') === 'modal';
    }).filter(function () {
        return $($(this).data('bs-target')).find('.input-summary').length > 0;
    }).on('click', function (e) {
        e.preventDefault();
        renderConfirmationPopup($($(this).data('bs-target')));
    });

    $('.form-confirmation-popup .submit-btn').on('click', function () {
        $(this).closest('.form-confirmation-popup').modal('hide');
        $('#' + $(this).data('form-target')).submit();
    });
}

function responsePopupsSetup() {
    const forms = $('form').filter(function () {
        return $(this).data('show-response-popups');
    });

    forms.on('submit-success', function (e, data) {
        const popup = $(`#${$(this).data('submit-success-popup')}`);
        renderResponsePopup(popup, data);
        popup.modal('show');
    });

    forms.on('submit-failure', function (e, data) {
        const popup = $(`#${$(this).data('submit-failure-popup')}`);
        renderResponsePopup(popup, data);
        popup.modal('show');
    });
}

// ---------------------------------------- ajax submit --------------------------------------- //

function handleAjaxSubmit(form) {
    $.ajax({
        type: 'POST',
        url: form.attr('action'),
        data: form.serialize(),
        success: function (data) {
            formRefresh(form);

            form.trigger('submit-complete', [data])

            if (data.status === 'success')
                form.trigger('submit-success', [data]);
            else {
                form.trigger('submit-failure', [data]);

                if (data.status === 'invalid')
                    form.trigger('submit-invalid', [data])
                else if (data.status === 'impermissible')
                    form.trigger('submit-impermissible', [data])
                else if (data.status === 'error')
                    form.trigger('submit-error', [data])
            }
        }
    });
}

// ----------------------------------- field & group toggle ----------------------------------- //

function toggleFieldButtonClickHandler(e, btn) {
    e.preventDefault();
    toggleTextSwitchBtn(btn);
    let on = false;
    const input = btn.closest('.input-group').find('input')

    if (btn.hasClass('switch-on'))
        on = true;

    toggleField(input, on);

    if (on)
        input.focus();

    submitButtonRefresh(btn.closest('form'));
}

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

function toggleGroupButtonClickHandler(e, btn) {
    e.preventDefault();
    toggleTextSwitchBtn(btn);
    let on = false;
    const group = btn.closest('.form-element-group');

    if (btn.hasClass('switch-on'))
        on = true;

    toggleFieldGroup(group, on)

    if (on)
        group.find('input:first').focus()

    submitButtonRefresh(btn.closest('form'));
}

function toggleFieldGroup(formElementGroup, on) {
    formElementGroup.find('input').each(function () {
        toggleField($(this), on)
    });
}

// --------------------------------------- form refresh --------------------------------------- //

function formRefresh(form) {
    form[0].reset();
    clearValidation(form);
    resetToggleables(form);
    submitButtonRefresh(form);
    resetHiddenFields(form);
}

function clearValidation(form) {
    form.find('input').removeClass('is-valid').removeClass('is-invalid');
    form.find('.invalid-feedback').remove();
}

function resetToggleables(form) {
    form.find('.field-toggle-btn').each(function () {
        toggleableFieldButtonInit($(this));
    });

    form.find('.group-toggle-btn').each(function () {
        toggleableGroupButtonInit($(this));
    });
}

function resetHiddenFields(form) {
    form.find('input[type="hidden"]').each(function () {
        if ($(this).data('reset-on-refresh') === true)
            $(this).val('');
    });

}

// -------------------------------------- live validation ------------------------------------- //

function update_validation_status(field, formCls, minLength, url) {
    const value = $(field).val();
    $.ajax({
        url: url,
        data: {
            'formCls': formCls,
            'fieldName': $(field).attr('name'),
            'value': value,
            'minLength': minLength,
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

            $(field).trigger('validation-complete');
        }
    });
}

function submitButtonRefresh(form) {
    if (form.find('.live-validation').filter(function () {
        return ($(this)).find('input:not(:disabled):not(.is-valid)').length > 0;
    }).length > 0)
        form.find('.submit-btn').attr('disabled', true);
    else
        enableSubmitButton(form.find('.submit-btn'));
}

function enableSubmitButton(submitButton) {
    if (submitButton.is(':disabled')) {
        submitButton.attr('disabled', false);
        submitButton.addClass('submit-enabled');

        setTimeout(function () {
            submitButton.removeClass('submit-enabled');
        }, 300);
    }
}

// ------------------------------------------ popups ------------------------------------------ //

function renderConfirmationPopup(popup) {
    popup.find('.input-summary-label').text(function () {
        return $('#' + $(this).data('input-target')).closest('.input-group')
            .find('label').text() + ':';
    });

    popup.find('.input-summary-value').text(function () {
        const value = $('#' + $(this).data('input-target')).val();
        return value.length > 0 ? value : '-';
    });
}

function renderResponsePopup(popup, data) {
    const message = popup.find('.popup-message');
    if (message.data('render-message') === true)
        message.text(data.message);
    if (data['status'] === 'invalid')
        renderValidationErrors(popup, data['errors']);
}

function renderValidationErrors(popup, errors) {
    const form = popup.closest('.form-wrapper').find('form')
    const messageBlock = popup.find('.popup-message-wrapper');
    const errorsBlock = $('<div class="popup-errors-wrapper"></div>');

    Object.entries(errors).forEach(([key, value]) => {
        const errorDiv = $('<div class="popup-error mt-2"></div>');
        let fieldLabel = form.find(`label[for="${key}"]`).text();

        if (fieldLabel.length === 0)
            fieldLabel = key;

        errorDiv.append(`<b>${fieldLabel}:</b>`);

        const nestedList = $('<ul class="mb-0"></ul>');
        value.forEach((nestedValue) => {
            nestedList.append(`<li>${nestedValue}</li>`);
        });

        errorDiv.append(nestedList);
        errorsBlock.append(errorDiv);
    });

    messageBlock.after(errorsBlock);
}

// ------------------------------------ table select field ------------------------------------ //

function tableSelectFieldSetup() {
    $('.table-select-field').each(function () {
        const tableSelectField = $(this);
        const table = tableSelectField.find('table');
        const input = tableSelectField.find('.input-group input');

        table.DataTable().on('init.dt', function () {
            table.find('.select').on('click', function () {
                tableSelectFieldCheckboxClickHandler(tableSelectField, input)
            });
        });

        input.on('validation-complete', function () {
           if ($(this).hasClass('is-valid'))
               tableSelectField.removeClass('is-invalid').addClass('is-valid');
           else if ($(this).hasClass('is-invalid'))
               tableSelectField.removeClass('is-valid').addClass('is-invalid');
           else
               tableSelectField.removeClass('is-valid').removeClass('is-invalid');
        });
    });
}

function tableSelectFieldCheckboxClickHandler(tableSelectField, input) {
    const tableWidget = window.tableWidgets[`#${tableSelectField.find('table').attr('id')}`];
    const ids = [];

    for (const row of tableWidget.getAllSelectedRows())
        ids.push($(row).data('record-id'));

    input.val(ids.join(',')).trigger('input');
}
