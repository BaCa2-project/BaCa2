function switchTheme(post_url, csrf_token) {
    const element = document.body;
    element.dataset.bsTheme = element.dataset.bsTheme === 'dark' ? 'light' : 'dark';
    if (element.classList.contains('dark-theme')) {
        element.classList.remove('dark-theme');
        element.classList.add('light-theme');
    } else {
        element.classList.remove('light-theme');
        element.classList.add('dark-theme');
    }
    postThemeSwitch(element, post_url, csrf_token);
}

function postThemeSwitch(element, post_url, csrf_token) {
    $.ajax({
        type: "POST",
        url: post_url,
        data: {
            csrfmiddlewaretoken: csrf_token,
            theme: element.dataset.bsTheme
        },
        success: function (data) {
            console.log(data);
        }
    })
}
