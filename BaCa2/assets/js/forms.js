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