function sideNavSetup() {
    $('.side-nav-link').click(function () {
        clickSidenavLink($(this));
    });

    let link;
    const tab = new URL(window.location.href).searchParams.get('tab');

    if (tab !== null)
        link = $(document.body).find('.side-nav-link[data-id="' + tab + '"]');
    if (link === undefined || link.length === 0)
        link = $(document.body).find('.side-nav-content')
                               .find('.tab-button:last')
                               .find('.side-nav-link:first');

    clickSidenavLink(link);
}

function clickSidenavLink(link) {
    const clicked_button = link.closest('.side-nav-button');
    const side_nav = clicked_button.closest('.side-nav-content');
    const active_button = side_nav.find('.active');
    const expanded_button = side_nav.find('.expanded');
    const active_link = active_button.find('.side-nav-link');
    let activated_link;

    if (clicked_button[0] === active_button[0] || clicked_button[0] === expanded_button[0])
        return;

    if (clicked_button.hasClass('sub-tabs')) {
        const activated_button = clicked_button.find('.sub-tab-button:first');
        activated_button.addClass('active');
        clicked_button.addClass('expanded');
        activated_link = activated_button.find('.side-nav-link');
        expanded_button.removeClass('expanded');
    } else {
        clicked_button.addClass('active')
        activated_link = clicked_button.find('.side-nav-link');
    }

    if (clicked_button.hasClass('sub-tab-button') &&
        !clicked_button.closest('.sub-tabs').hasClass('expanded')) {
        clicked_button.closest('.sub-tabs').addClass('expanded');
        expanded_button.removeClass('expanded');
    } else if (clicked_button.hasClass('tab-button')) {
        expanded_button.removeClass('expanded');
    }

    $(document.body).find('#' + active_link.data('id')).removeClass('active');
    $(document.body).find('#' + activated_link.data('id')).addClass('active');
    active_button.removeClass('active');
    addURLParameter(activated_link.data('id'));
}

function toggleSidenavButton(button, textCollapsed, textExpanded) {
    const side_nav = $(document.body).find('.side-nav');
    if (side_nav.hasClass('collapsed')) {
        side_nav.removeClass('collapsed');
        side_nav.addClass('expanded');
        $(button).text(textExpanded);
    } else {
        side_nav.removeClass('expanded');
        side_nav.addClass('collapsed');
        $(button).text(textCollapsed);
    }
}

function addURLParameter(param) {
    const url = new URL(window.location.href);
    url.searchParams.set('tab', param);
    window.history.replaceState({}, '', url);
}
