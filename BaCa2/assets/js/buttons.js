function setUpTextSwitchBtn(btn) {
    const textOn = btn.data('text-on');
    const textOff = btn.data('text-off');
    const longerText = textOn.length > textOff.length ? textOn : textOff;
    const temp = $('<span>').css({visibility: 'hidden', whiteSpace: 'nowrap'}).text(longerText);

    $('body').append(temp);
    btn.width(temp.width());
    temp.remove();

    if (btn.hasClass('switch-off'))
        btn.text(textOff);
    else
        btn.text(textOn);
}

function toggleTextSwitchBtn(btn) {
    if (btn.hasClass('switch-on'))
        btn.removeClass('switch-on').addClass('switch-off');
    else
        btn.removeClass('switch-off').addClass('switch-on');

    btn.text(btn.hasClass('switch-on') ? btn.data('text-on') : btn.data('text-off'))
}

function buttonsSetup() {
    $('.text-switch-btn').each(function () {
        setUpTextSwitchBtn($(this))
    })
}
