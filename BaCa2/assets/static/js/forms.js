class FormInput {
    constructor(input, formWidget) {
        this.formWidget = formWidget;
        this.input = input;
        this.inputId = input.attr('id');
        this.required = input.prop('required');
        this.defaultVal = this.getDefaultVal();
        this.liveValidation = input.data('live-validation');
        this.toggleBtn = input.closest('.input-group').find('.field-toggle-btn');
        this.toggleable = this.toggleBtn.length > 0;

        const label = input.closest('form').find(`label[for="${this.inputId}"`)
        this.label = label.length > 0 ? label : null;
    }

    formInputInit() {
        this.toggleInit();
        this.liveValidationInit();
    }

    toggleInit() {
        if (!this.toggleable) return;
        const formInput = this;
        formInput.resetToggleable();

        this.toggleBtn.on('click', function (e) {
            e.preventDefault();
            console.log('toggle clicked');
            toggleTextSwitchBtn($(this));
            formInput.toggleInput($(this).hasClass('switch-on'), true);
        });
    }

    liveValidationInit() {
        if (!this.liveValidation) return;
        if (this.hasValue()) this.setValid();
    }

    getLabel() {
        if (!this.label) return this.inputId;
        let label = this.label

        if (this.label.find('.required-symbol').length > 0) {
            label = label.clone();
            label.find('.required-symbol').remove();
        }

        return label.text().trim();
    }

    getDefaultVal() {
        const defaultVal = this.input.prop('defaultValue');
        return defaultVal !== undefined ? defaultVal : '';
    }

    getVal() {
        return this.input.val();
    }

    hasValue() {
        const val = this.getVal();
        return val !== undefined && val !== null && val.length > 0;
    }

    setValid() {
        if (!this.liveValidation) return;
        this.input.removeClass('is-invalid').addClass('is-valid');
    }

    setInvalid() {
        if (!this.liveValidation) return;
        this.input.removeClass('is-valid').addClass('is-invalid');
    }

    clearValidation() {
        this.input.removeClass('is-valid').removeClass('is-invalid');
        this.input.closest('.input-block').find('.invalid-feedback').remove();
    }

    isValid() {
        if (this.input.hasClass('is-invalid')) return false;
        return !(this.required && !this.hasValue());
    }

    resetValue() {
        if (this.defaultVal.length > 0) {
            this.input.val(this.defaultVal);
            this.setValid();
        } else
            this.clearValue();
    }

    clearValue() {
        this.input.val('');
        this.clearValidation();
    }

    resetInput() {
        this.resetValue();
        this.resetToggleable();
    }

    resetToggleable() {
        if (!this.toggleable) return;
        let on = this.toggleBtn.data('initial-state') !== 'off';

        if (this.toggleBtn.hasClass('switch-on') && !on)
            toggleTextSwitchBtn(this.toggleBtn);

        this.toggleInput(on);
    }

    toggleInput(on, focus = false) {
        if (on) {
            this.input.attr('disabled', false);
            this.resetValue();
            if (focus) this.input.focus();
        } else {
            this.clearValue()
            this.input.attr('disabled', true);
        }
    }
}


class SelectInput extends FormInput {
    constructor(input, formWidget) {
        super(input, formWidget);
        this.autoWidth = input.hasClass('auto-width');
        this.placeholderOption = input.data('placeholder-option');
    }

    formInputInit() {
        super.formInputInit();
        this.autoWidthInit();
        this.placeholderOptionInit();
    }

    autoWidthInit() {
        if (!this.autoWidth) return;
        const select = this.input;
        const tempDiv = $('<div></div>').css({'position': 'absolute', 'visibility': 'hidden'});
        const tempOption = $('<option class="d-flex"></option>');
        tempDiv.appendTo('body');
        tempOption.appendTo(tempDiv);
        tempOption.text(this.placeholderOption || '');

        select.find('option').each(function () {
            tempOption.text($(this).text());

            if (tempOption.width() > select.width())
                select.width(tempOption.width());
        });

        tempDiv.remove()
    }

    placeholderOptionInit() {
        if (!this.placeholderOption) return;
        this.input.prepend(
            `<option class="placeholder" value="" selected>${this.placeholderOption}</option>`
        );
    }

    liveValidationInit() {
        if (!this.liveValidation) return;
        if (!this.placeholderOption) this.setValid();

        const selectInput = this;

        this.input.on('input', function () {
            selectInput.validateInput();
        });
    }

    validateInput() {
        if (this.hasValue()) {
            this.setValid();
            this.formWidget.refreshSubmitBtn();
        }
        else {
            this.setInvalid();
            this.formWidget.disableSubmitBtn();
        }

        this.input.trigger('validation-complete');
    }

    getDefaultVal() {
        const selectedOption = this.input.find('option:selected');
        return selectedOption.length > 0 ? selectedOption.val() : '';
    }
}


class TableSelectField extends FormInput {
    constructor(input, formWidget) {
        super(input, formWidget);
        this.wrapper = input.closest('.table-select-field');
        this.tableId = input.data('table-id');
        this.tableWidget = window.tableWidgets[`#${this.tableId}`];
    }

    setValid() {
        if (!this.liveValidation) return;
        this.input.removeClass('is-invalid').addClass('is-valid');
        this.wrapper.removeClass('is-invalid').addClass('is-valid');
    }

    setInvalid() {
        if (!this.liveValidation) return;
        this.input.removeClass('is-valid').addClass('is-invalid');
        this.wrapper.removeClass('is-valid').addClass('is-invalid');
    }

    clearValidation() {
        this.input.removeClass('is-valid').removeClass('is-invalid');
        this.wrapper.removeClass('is-valid').removeClass('is-invalid');
    }
}


class FormPopup {
    constructor(popup, formWidget) {
        this.popup = popup;
        this.formWidget = formWidget;
    }

    render(data = null) {
        this.popup.modal('show');
    }
}


class ConfirmationPopup extends FormPopup {
    constructor(popup, formWidget) {
        super(popup, formWidget);
        const inputSummary = {};

        this.popup.find('.input-summary').each(function () {
            const inputId = $(this).data('input-target');
            const inputLabel = $(this).find('.input-summary-label');
            const inputVal = $(this).find('.input-summary-value');
            inputSummary[inputId] = {label: inputLabel, value: inputVal};
        });

        this.inputSummary = inputSummary;
        this.submitBtn = this.popup.find('.submit-btn');
    }

    render(data = null) {
        const inputSummary = this.inputSummary;

        this.formWidget.getInputs(Object.keys(this.inputSummary)).each(function () {
            const summary = inputSummary[this.inputId];
            const val = this.getVal();
            summary.label.text(this.getLabel() + ':');
            summary.value.text(val.length > 0 ? val : '-');
        });

        super.render();
    }
}


class ResponsePopup extends FormPopup {
    constructor(popup, formWidget) {
        super(popup, formWidget);
        this.message = this.popup.find('.popup-message');
        this.messageBlock = this.popup.find('.popup-message-wrapper');
        this.renderMessage = this.message.data('render-message') === true;
    }

    render(data) {
        if (this.renderMessage)
            this.message.text(data.message);
        if (data['status'] === 'invalid')
            this.renderValidationErrors(data);
        else if (data['status'] === 'error')
            this.renderErrorMessages(data);
        super.render(data);
    }

    renderValidationErrors(data) {
        this.popup.find('.popup-errors-wrapper').remove();
        const errorsBlock = $('<div class="popup-errors-wrapper"></div>');

        Object.entries(data.errors).forEach(([key, value]) => {
            const errorDiv = $('<div class="popup-error mt-2"></div>');
            const nestedList = $('<ul class="mb-0"></ul>');
            const fieldLabel = this.formWidget.inputs[key].getLabel();


            value.forEach((nestedValue) => {
                nestedList.append(`<li>${nestedValue}</li>`);
            });

            errorDiv.append(`<b>${fieldLabel}:</b>`);
            errorDiv.append(nestedList);
            errorsBlock.append(errorDiv);
        });

        this.messageBlock.after(errorsBlock);
    }

    renderErrorMessages(data) {
        this.popup.find('.popup-errors-wrapper').remove();
        const errorsBlock = $('<div class="popup-errors-wrapper text-center"></div>');

        data.errors.forEach((error) => {
            errorsBlock.append(`<div class="popup-error mt-2"><b>${error}</b></div>`);
        });

        this.messageBlock.after(errorsBlock);
    }
}


class FormWidget {
    constructor(form) {
        this.form = form;
        this.wrapper = form.closest('.form-wrapper');
        this.submitBtn = form.find('.submit-btn');
        this.ajaxSubmit = form.attr('action') !== undefined;
        this.resetOnSubmit = form.data('reset-on-submit');
        this.postUrl = this.ajaxSubmit ? form.attr('action') : null;
        this.inputs = this.getInputs().get().reduce((dict, input) => {
            dict[input.inputId] = input;
            return dict;
        }, {});

        const confirmationPopup = this.wrapper.find('.form-confirmation-popup');
        this.confirmationPopup = confirmationPopup.length > 0 ?
                                 new ConfirmationPopup(confirmationPopup, this) : null;

        this.showResponsePopups = this.form.data('show-response-popups');
        this.successPopup = this.showResponsePopups ?
                            new ResponsePopup(this.wrapper.find('.form-success-popup'), this) :
                            null;
        this.failurePopup = this.showResponsePopups ?
                            new ResponsePopup(this.wrapper.find('.form-failure-popup'), this) :
                            null;
    }

    formWidgetInit() {
        this.submitHandlingInit();
        this.submitBtnInit();
        this.refreshBtnInit();
        this.responsePopupsInit();
        this.toggleableGroupInit();

        for (const input of Object.values(this.inputs))
            input.formInputInit();

        this.refreshSubmitBtn();
    }

    submitHandlingInit() {
        if (!this.ajaxSubmit) return;
        const formWidget = this;

        this.form.on('submit', function (e) {
            e.preventDefault();
            formWidget.handleAjaxSubmit();
        });
    }

    submitBtnInit() {
        if (this.confirmationPopup) {
            const popup = this.confirmationPopup
            const formWidget = this;

            this.submitBtn.on('click', function (e) {
                e.preventDefault();
                popup.render();
            });

            this.confirmationPopup.submitBtn.on('click', function () {
                popup.popup.modal('hide');
                formWidget.submit();
            });
        }
    }

    refreshBtnInit() {
        const formWidget = this;
        this.form.find('.form-refresh-button').on('click', function () {
            formWidget.resetForm();
        });
    }

    responsePopupsInit() {
        if (!this.showResponsePopups) return;
        const successPopup = this.successPopup;
        const failurePopup = this.failurePopup;

        this.form.on('submit-success', function (e, data) {
            successPopup.render(data);
        });

        this.form.on('submit-failure', function (e, data) {
            failurePopup.render(data);
        });
    }

    toggleableGroupInit() {
        const formWidget = this;

        this.form.find('.group-toggle-btn').each(function () {
            const btn = $(this);
            formWidget.resetToggleableGroup(btn);


            btn.on('click', function (e) {
                e.preventDefault();
                toggleTextSwitchBtn(btn);
                formWidget.toggleElementGroup(btn.closest('.form-element-group'),
                                              btn.hasClass('switch-on'));
                formWidget.refreshSubmitBtn();
            });
        });
    }

    resetToggleableGroups() {
        const formWidget = this;

        this.form.find('.group-toggle-btn').each(function () {
            formWidget.resetToggleableGroup($(this));
        });
    }

    resetToggleableGroup(toggleBtn) {
        const on = toggleBtn.data('initial-state') !== 'off';
        const elementGroup = toggleBtn.closest('.form-element-group');
        if (toggleBtn.hasClass('switch-on') && !on) toggleTextSwitchBtn(toggleBtn);
        this.toggleElementGroup(elementGroup, on);
    }

    toggleElementGroup(elementGroup, on) {
        this.getElementGroupInputs(elementGroup).each(function () {
            this.toggleInput(on);
        });
    }

    submit() {
        this.form.submit();
    }

    handleAjaxSubmit() {
        const loaderModal = $('#loader-modal');
        const formWidget = this;
        const formData = new FormData(formWidget.form[0]);

        loaderModal.one('shown.bs.modal', function () {
            $.ajax({
                       type: 'POST',
                       url: formWidget.postUrl,
                       data: formData,
                       contentType: false,
                       processData: false,
                       success: function (data) {
                           loaderModal.modal('hide');

                           if (formWidget.resetOnSubmit)
                               formWidget.resetForm();
                           else
                               formWidget.submitBtn.attr('disabled', true);

                           formWidget.form.trigger('submit-complete', [data]);

                           if (data.status === 'success') {
                               formWidget.form.trigger('submit-success', [data]);
                               return;
                           }

                           formWidget.form.trigger('submit-failure', [data]);

                           switch (data.status) {
                               case 'invalid':
                                   formWidget.form.trigger('submit-invalid', [data]);
                                   break;
                               case 'impermissible':
                                   formWidget.form.trigger('submit-impermissible', [data]);
                                   break;
                               case 'error':
                                   formWidget.form.trigger('submit-error', [data]);
                                   break;
                           }
                       },
                       error: function (jqxhr, settings, thrownError) {
                           loaderModal.modal('hide');
                           console.log('ajax submit error', jqxhr, settings, thrownError);
                       }
                   });
        });

        loaderModal.modal('show');
    }

    getInputs(ids = null) {
        const formWidget = this;

        if (ids) {
            if (Array.isArray(ids))
                ids = ids.map(id => `#${id}`).join(', ');
            return this.form.find(ids).map(function () {
                return formWidget.getInputObj($(this));
            });
        }

        return this.form.find('input, select, textarea').map(function () {
            return formWidget.getInputObj($(this));
        });
    }

    getElementGroupInputs(elementGroup) {
        const formWidget = this;

        return elementGroup.find('input, select, textarea').map(function () {
            return formWidget.getInputObj($(this));
        });
    }

    getInputObj(inputElement) {
        if (inputElement.hasClass('table-select-input'))
            return new TableSelectField(inputElement, this);
        else if (inputElement.is('select'))
            return new SelectInput(inputElement, this);
        else
            return new FormInput(inputElement, this);
    }

    refreshSubmitBtn() {
        for (const input of Object.values(this.inputs))
            if (!input.isValid()) {
                this.submitBtn.attr('disabled', true);
                return;
            }

        this.enableSubmitBtn();
    }

    enableSubmitBtn() {
        const submitBtn = this.submitBtn;

        if (submitBtn.is(':disabled')) {
            submitBtn.attr('disabled', false).addClass('submit-enabled');

            setTimeout(function () {
                submitBtn.removeClass('submit-enabled');
            }, 300);
        }
    }

    disableSubmitBtn() {
        this.submitBtn.attr('disabled', true);
    }

    resetForm() {
        for (const input of Object.values(this.inputs))
            input.resetInput();
        this.resetToggleableGroups();
        this.refreshSubmitBtn();
    }
}


$(document).ready(function () {
   $(':not(form) select.auto-width').each(function () {
        const selectInput = new SelectInput($(this), null);
        selectInput.autoWidthInit();
   });
});


// ---------------------------------------- forms setup --------------------------------------- //

function formsPreSetup() {
    tableSelectFieldSetup();

    $(document).on('tab-activated', function (e) {
        const tab = $(e.target);
        tab.find('.model-choice-field').each(function () {
            loadModelChoiceFieldOptions($(this));
        });
    });
}

function formsSetup() {
    $('form').each(function () {
        new FormWidget($(this)).formWidgetInit();
    });

    modelChoiceFieldSetup();
    textAreaFieldSetup();
    tableSelectFieldValidationSetup();
    formObserverSetup();
}

function textAreaFieldSetup() {
    $('.form-floating textarea').each(function () {
        const rows = $(this).attr('rows');
        const height = `${rows * 2.1}rem`;
        $(this).css('height', height);
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

// --------------------------------------- form observer -------------------------------------- //

function formObserverSetup() {
    formObserverElementGroupSetup();
    formObserverListenerSetup();
}

function formObserverListenerSetup() {
    $('.form-observer').each(function () {
        const observer = $(this);
        const formId = observer.data('form-id');
        const form = $(`#${formId}`);

        form.find('input, select, textarea').change(function () {
            formObserverFieldChangeHandler(observer, form, $(this));
        });
    });
}

function formObserverElementGroupSetup() {
    $('.form-observer[data-element-group-titles="true"]').each(function () {
        const observer = $(this);
        const formId = observer.data('form-id');
        const form = $(`#${formId}`);
        const summary = observer.find('.observer-summary');

        form.find('.form-element-group[data-title!=""]').each(function () {
            const groupId = $(this).attr('id');
            const groupTitle = $(this).data('title');

            summary.each(function () {
                const groupSummary = $('<div class="group-summary"></div>');

                groupSummary.attr('data-group-id', groupId);
                groupSummary.append(`<h6 class="group-title">${groupTitle}</h6>`);
                groupSummary.append('<div class="group-fields row"></div>');

                $(this).append(groupSummary);
            });
        });
    });
}

function formObserverFieldChangeHandler(observer, form, field) {
    updateFormObserverSummary(observer,
                              observer.find('.observer-general-summary:first'),
                              form,
                              field);

    observer.find('.form-observer-tab-content').each(function () {
        const acceptedFields = $(this).data('fields').split(' ');

        if (acceptedFields.includes(field.attr('name')))
            updateFormObserverSummary(observer, $(this), form, field);
    });
}

function updateFormObserverSummary(observer, summary, form, field) {
    let targetDiv = summary;

    if (observer.data('element-group-titles')) {
        const group = getClosestTitledElementGroup(field);

        if (group !== null) {
            targetDiv = summary.find(`.group-summary[data-group-id="${group.attr('id')}"]`);
            targetDiv = targetDiv.find('.group-fields');
        }
    }

    let fieldSummary = targetDiv.find(`.field-summary[data-field-id="${field.attr('id')}"]`);
    let fieldVal = field.val();
    const fieldDefaultVal = field.prop("defaultValue");

    if (fieldSummary.length > 0)
        return updateFormObserverFieldSummary(targetDiv, fieldSummary, fieldVal, fieldDefaultVal);


    const fieldLabel = getFieldLabel(field.attr('id'), form);
    const valueSummary = $(`<div class="row justify-content-center"></div>`);

    fieldVal = fieldVal === '' ? '<i class="bi bi-x-lg"></i>' : fieldVal;

    fieldSummary = $('<div class="field-summary col"></div>');
    fieldSummary.attr('data-field-id', field.attr('id'));
    fieldSummary.append(`<div class="field-label row"><b>${fieldLabel}:</b></div>`);

    valueSummary.append(`<div class="field-default-value col-auto">${fieldDefaultVal}</div>`);
    valueSummary.append(`<div class="col-auto"><i class="bi bi-arrow-right"></i></div>`);
    valueSummary.append(`<div class="field-value col-auto">${fieldVal}</div>`);

    targetDiv.prepend(fieldSummary.append(valueSummary));
    targetDiv.closest('.group-summary').addClass('has-fields');
}

function updateFormObserverFieldSummary(summaryDiv, summary, fieldVal, fieldDefaultVal) {
    if (fieldVal === fieldDefaultVal) {
        summary.remove();

        if (summaryDiv.find('.field-summary').length === 0)
            summaryDiv.closest('.group-summary').removeClass('has-fields');
    } else
        summary.find('.field-value')
               .text(fieldVal === '' ? '<i class="bi bi-x-lg"></i>' : fieldVal);
}

function getClosestTitledElementGroup(field) {
    return field.closest('.form-element-group[data-title]:not([data-title=""])');
}

// ------------------------------------ table select field ------------------------------------ //

function tableSelectFieldSetup() {
    $(document).on('init.dt table-reload', function (e) {
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

                tableWidget.DTObj.ajax.reload(function () {
                    $(`#${tableId}`).trigger('table-reload');
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

// ------------------------------------ model choice field ------------------------------------ //

function modelChoiceFieldSetup() {
    $('.model-choice-field').each(function () {
        loadModelChoiceFieldOptions($(this));
    });

    $('.model-choice-field-reload-btn').each(function () {
        const field = $(this).closest('.input-group').find('.model-choice-field');
        $(this).on('click', function () {
            loadModelChoiceFieldOptions(field);
        });
    });
}

function loadModelChoiceFieldOptions(field) {
    if (field.hasClass('loading')) return;
    field.addClass('loading');

    const sourceURL = field.data('source-url');
    const labelFormatString = field.data('label-format-string');
    const valueFormatString = field.data('value-format-string');
    const placeholderOption = field.find('option.placeholder');
    const placeholderText = placeholderOption.text();

    field.removeClass('is-valid').removeClass('is-invalid');
    field.attr('disabled', true);
    placeholderOption.text(field.data('loading-option'));

    $.ajax({
               url: sourceURL,
               dataType: 'json',
               success: function (response) {
                   field.find('option:not(.placeholder)').remove();

                   for (const record of response.data) {
                       addModelChoiceFieldOption(field,
                                                 record,
                                                 labelFormatString,
                                                 valueFormatString)
                   }

                   placeholderOption.text(placeholderText);
                   field.attr('disabled', false);
                   field.removeClass('loading');
               }
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
