// ---------------------------------------- forms setup --------------------------------------- //

function formsPreSetup() {
    tableSelectFieldSetup();
}

function formsSetup() {
    ajaxPostSetup();
    toggleableGroupSetup();
    toggleableFieldSetup();
    confirmationPopupSetup();
    responsePopupsSetup();
    refreshButtonSetup();
    selectFieldSetup();
    choiceFieldSetup();
    modelChoiceFieldSetup();
    textAreaFieldSetup();
    liveValidationSetup();
    tableSelectFieldValidationSetup();
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
        const form = $(this);
        form.find('.form-refresh-button').on('click', function () {
            formRefresh(form);
        });
    });
}

function liveValidationSetup() {
    $('form').each(function () {
        $(this).find('.live-validation').each(function () {
            $(this).find('input').filter(function () {
                return $(this).val() !== undefined && $(this).val().length > 0;
            }).addClass('is-valid');

            $(this).find('textarea').filter(function () {
                return $(this).val() !== undefined && $(this).val().length > 0;
            }).addClass('is-valid');

            $(this).find('select').filter(function () {
                return $(this).val() !== null && $(this).val().length > 0;
            }).addClass('is-valid');
        })
        submitButtonRefresh($(this));
    });
}

function textAreaFieldSetup() {
    $('.form-floating textarea').each(function () {
        const rows = $(this).attr('rows');
        const height = `${rows * 2.1}rem`;
        $(this).css('height', height);
    });
}

// --------------------------------------- toggle setup --------------------------------------- //

function toggleableFieldSetup() {
    const buttons = $('.field-toggle-btn');

    buttons.each(function () {
        toggleableFieldButtonInit($(this));
    });

    buttons.on('click', function (e) {
        toggleFieldButtonClickHandler(e, $(this));
    });
}

function toggleableFieldButtonInit(button) {
    let on = button.data('initial-state') !== 'off';
    if (button.hasClass('switch-on') && !on)
        toggleTextSwitchBtn(button);
    toggleField(button.closest('.input-group').find('input'), on);
}

function toggleableGroupSetup() {
    const buttons = $('.group-toggle-btn');

    buttons.each(function () {
        toggleableGroupButtonInit($(this));
    });

    buttons.on('click', function (e) {
        toggleGroupButtonClickHandler(e, $(this));
    });
}

function toggleableGroupButtonInit(button) {
    let on = button.data('initial-state') !== 'off';
    if (button.hasClass('switch-on') && !on)
        toggleTextSwitchBtn(button);
    toggleFieldGroup(button.closest('.form-element-group'), on);
}

// ---------------------------------------- popup setup --------------------------------------- //

function confirmationPopupSetup() {
    const formWrappers = $('.form-wrapper').filter(function () {
        return $(this).find('.form-confirmation-popup').length > 0;
    });

    formWrappers.each(function () {
        const form = $(this).find('form');
        const popup = $(this).find('.form-confirmation-popup');
        const submitBtn = form.find('.submit-btn');
        submitBtn.on('click', function (e) {
            e.preventDefault();
            renderConfirmationPopup(popup, form);
        });
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
    const formData = new FormData(form[0]);
    $.ajax({
               type: 'POST',
               url: form.attr('action'),
               data: formData,
               contentType: false,
               processData: false,
               success: function (data) {
                   formRefresh(form);

                   form.trigger('submit-complete', [data]);

                   if (data.status === 'success')
                       form.trigger('submit-success', [data]);
                   else {
                       form.trigger('submit-failure', [data]);

                       if (data.status === 'invalid')
                           form.trigger('submit-invalid', [data]);
                       else if (data.status === 'impermissible')
                           form.trigger('submit-impermissible', [data]);
                       else if (data.status === 'error')
                           form.trigger('submit-error', [data]);
                   }
               }
           });
}

// ----------------------------------- field & group toggle ----------------------------------- //

function toggleFieldButtonClickHandler(e, btn) {
    e.preventDefault();
    toggleTextSwitchBtn(btn);
    let on = false;
    const input = btn.closest('.input-group').find('input');

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
        field.removeClass('is-valid');
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

    toggleFieldGroup(group, on);

    if (on)
        group.find('input:first').focus();

    submitButtonRefresh(btn.closest('form'));
}

function toggleFieldGroup(formElementGroup, on) {
    formElementGroup.find('input').each(function () {
        toggleField($(this), on);
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
    form.find('select').removeClass('is-valid').removeClass('is-invalid');
    form.find('textarea').removeClass('is-valid').removeClass('is-invalid');
    form.find('.table-select-field').removeClass('is-valid').removeClass('is-invalid');
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

function updateValidationStatus(field, formCls, formInstanceId, minLength, url) {
    const value = $(field).val();
    $.ajax({
               url: url,
               data: {
                   'formCls': formCls,
                   'form_instance_id': formInstanceId,
                   'fieldName': $(field).attr('name'),
                   'value': value,
                   'minLength': minLength,
               },
               dataType: 'json',
               success: function (data) {
                   if (data.status === 'ok') {
                       $(field).removeClass('is-invalid');

                       if (value.length > 0)
                           $(field).addClass('is-valid');
                       else
                           $(field).removeClass('is-valid');

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

function updateSelectFieldValidationStatus(field) {
    if ($(field).val().length === 0) {
        $(field).removeClass('is-valid');
        $(field).addClass('is-invalid');
        $(field).closest('form').find('.submit-btn').attr('disabled', true);
    } else {
        $(field).removeClass('is-invalid');
        $(field).addClass('is-valid');
        submitButtonRefresh($(field).closest('form'));
    }

    $(field).trigger('validation-complete');
}

function submitButtonRefresh(form) {
    if (form.find('.live-validation').filter(function () {
        return ($(this)).find('input:not(:disabled):not(.is-valid):required').length > 0 ||
               $(this).find('select:not(:disabled):not(.is-valid)').length > 0;
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

function renderConfirmationPopup(popup, form) {
    popup.find('.input-summary-label').text(function () {
        const inputId = $(this).data('input-target');
        return getFieldLabel(inputId, form) + ':';
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
    if (data['status'] === 'error')
        renderErrorMessages(popup, data['errors']);
}

function renderErrorMessages(popup, errors) {
    const messageBlock = popup.find('.popup-message-wrapper');
    const errorsBlock = $('<div class="popup-errors-wrapper text-center"></div>');

    errors.forEach((error) => {
        errorsBlock.append(`<div class="popup-error mt-2"><b>${error}</b></div>`);
    });

    messageBlock.after(errorsBlock);
}

function renderValidationErrors(popup, errors) {
    const form = popup.closest('.form-wrapper').find('form');
    const messageBlock = popup.find('.popup-message-wrapper');
    const errorsBlock = $('<div class="popup-errors-wrapper"></div>');

    Object.entries(errors).forEach(([key, value]) => {
        const errorDiv = $('<div class="popup-error mt-2"></div>');
        const fieldLabel = getFieldLabel(key, form);

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
    $(document).on('init.dt', function (e) {
        const table = $(e.target);

        table.closest('.table-select-field').each(function () {
            const tableSelectField = $(this);
            const tableId = table.attr('id');
            const input = tableSelectField.find('.input-group input');
            const inputVal = input.val();
            const form = tableSelectField.closest('form');
            const tableWidget = window.tableWidgets[`#${tableId}`];

            table.find('.select').on('change', function () {
                tableSelectFieldCheckboxClickHandler(tableSelectField, input);
            });

            form.on('submit-complete', function () {
                tableWidget.table.one('draw.dt', function () {
                    tableWidget.updateSelectHeader();
                });

                tableWidget.table.ajax.reload(function () {
                    $(`#${tableId}`).trigger('init.dt');
                });
            })

            if (inputVal.length > 0) {
                const recordIds = inputVal.split(',');

                for (const id of recordIds) {
                    const row = table.find(`tr[data-record-id="${id}"]`);
                    const checkbox = row.find('.select .select-checkbox');
                    row.addClass('row-selected');
                    checkbox.prop('checked', true);
                }

                tableWidget.updateSelectHeader();
            }
        });
    });
}

function tableSelectFieldValidationSetup() {
    $('.table-select-field').each(function () {
        const tableSelectField = $(this);
        const input = tableSelectField.find('.input-group input');

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
    const tableId = input.data('table-id');
    const tableWidget = window.tableWidgets[`#${tableId}`];
    const ids = [];

    for (const row of tableWidget.getAllSelectedRows())
        ids.push($(row).data('record-id'));

    input.val(ids.join(',')).trigger('input');
}

// --------------------------------------- select field --------------------------------------- //

function selectFieldSetup() {
    $('select.auto-width').each(function () {
        const select = $(this);
        const tempDiv = $('<div></div>').css({'position': 'absolute', 'visibility': 'hidden'});
        const tempOption = $('<option class="d-flex"></option>');
        tempDiv.appendTo('body');
        tempOption.appendTo(tempDiv);
        tempOption.text(select.data('placeholder-option'));

        select.find('option').each(function () {
            tempOption.text($(this).text());

            if (tempOption.width() > select.width())
                select.width(tempOption.width());
        });

        tempDiv.remove();
    });
}

// ------------------------------------ model choice field ------------------------------------ //

function choiceFieldSetup() {
    $('.choice-field.placeholder-option').each(function () {
        const placeholder = $(this).data('placeholder-option');
        $(this).prepend(`<option class="placeholder" value="" selected>${placeholder}</option>`);
    });

    $('.choice-field:not(.placeholder-option)').each(function () {
        const inputBlock = $(this).closest('.input-block');
        if (inputBlock.find('.live-validation').length > 0)
            updateSelectFieldValidationStatus($(this));
    });
}

function modelChoiceFieldSetup() {
    $('.model-choice-field').each(function () {
        const field = $(this);
        const sourceURL = field.data('source-url');
        const labelFormatString = field.data('label-format-string');
        const valueFormatString = field.data('value-format-string');
        const placeholderOption = field.find('option.placeholder');
        const placeholderText = placeholderOption.text();

        field.attr('disabled', true);
        placeholderOption.text(field.data('loading-option'));

        $.ajax({
                   url: sourceURL,
                   dataType: 'json',
                   success: function (response) {
                       for (const record of response.data) {
                           addModelChoiceFieldOption(field,
                                                     record,
                                                     labelFormatString,
                                                     valueFormatString)
                       }

                       placeholderOption.text(placeholderText);
                       field.attr('disabled', false);
                   }
               })
    })
}

function addModelChoiceFieldOption(field, data, labelFormatString, valueFormatString) {
    const value = generateFormattedString(data, valueFormatString);
    const label = generateFormattedString(data, labelFormatString);
    field.append(`<option value="${value}">${label}</option>`);
}

// ------------------------------------------ helpers ----------------------------------------- //

function getFieldLabel(fieldId, form) {
    let label = form.find(`label[for="${fieldId}"]`);

    if (label.length === 0)
        return fieldId;

    if (label.find('.required-symbol').length > 0) {
        label = label.clone();
        label.find('.required-symbol').remove();
    }

    return label.text().trim();
}
