$(document).ready(function () {
    $('.side-nav-link').click(function () {
        const clicked_button = $(this).closest('.side-nav-button');
        const side_nav = clicked_button.closest('.side-nav-content');
        const active_button = side_nav.find('.active');
        const active_link = active_button.find('.side-nav-link');
        const active_tab = $(document.body).find('#' + active_link.data('id'));
        const activated_tab = $(document.body).find('#' + $(this).data('id'));

        active_button.removeClass('active');
        active_tab.removeClass('active');
        clicked_button.addClass('active');
        activated_tab.addClass('active');
    });

    $('.side-nav-button').hover(function () {
        const sub_tabs_wrapper = $(this).find('.sub-tabs-wrapper');
        if (sub_tabs_wrapper.length) {
            sub_tabs_wrapper.addClass('expanded');
        }
    }, function () {
        const sub_tabs_wrapper = $(this).find('.sub-tabs-wrapper');
        if (sub_tabs_wrapper.length) {
            sub_tabs_wrapper.removeClass('expanded');
        }
    });

    const active_link = $(document.body).find('.side-nav-content').find('.active').find('.side-nav-link');
    const active_tab = $(document.body).find('#' + active_link.data('id'));
    active_tab.addClass('active');
});