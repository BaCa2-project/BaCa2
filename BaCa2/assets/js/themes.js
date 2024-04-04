function themePreSetup() {
    $(document).on('theme-switched', function (e, theme) {
        codeHighlightingThemeSwitch(theme);
    });
}

function themeSetup() {
    codeHighlightingThemeSwitch($('body').attr('data-bs-theme'));
}

function codeHighlightingThemeSwitch(theme) {
    $('link.code-highlighting').attr("disabled", true);
    $('link.code-highlighting[data-bs-theme=' + theme + ']').removeAttr("disabled");
}

function switchTheme(post_url, csrf_token) {
    const body = $('body');
    const theme = body.attr('data-bs-theme') === 'dark' ? 'light' : 'dark';

    body.attr('data-bs-theme', theme);
    body.removeClass('dark-theme light-theme').addClass(theme + '-theme');
    body.trigger('theme-switched', theme);

    postThemeSwitch(body, post_url, csrf_token);
}

function postThemeSwitch(body, post_url, csrf_token) {
    $.ajax({
        type: "POST",
        url: post_url,
        data: {
            csrfmiddlewaretoken: csrf_token,
            theme: body.attr('data-bs-theme')
        },
        success: function (data) {
            console.log(data);
        }
    })
}
