function sidenavSetup() {
    const sidenavTabs = $('.sidenav').find('.sidenav-tabs');

    if (sidenavTabs.length === 0)
        return;

    $(document).ready(function () {
        function setSubTabsHeight() {
            $('.sub-tabs-wrapper').each(function () {
                $(this).css('height', sidenavTabs.height() + 'px')
            });
        }

        setSubTabsHeight();

        $(window).resize(function () {
            console.log('resize');
            setSubTabsHeight();
        });
    });

    $('.sidenav-tab:not(.has-sub-tabs)').click(function () {
        sidenavTabClickHandler($(this));
    });

    const tabID = new URL(window.location.href).searchParams.get('tab');

    if (tabID !== null) {
        const tab = $(`#${tabID}`);
        if (tab.length > 0)
            sidenavTabClickHandler(tab);
    } else {
        const firstTab = $('.sidenav-tab:not(.has-sub-tabs):first');
        sidenavTabClickHandler(firstTab);
    }
}

function sidenavTabClickHandler(tab) {
    const sidenav = tab.closest('.sidenav');
    const activeTab = sidenav.find('.sidenav-tab.active');

    if (activeTab[0] === tab[0])
        return;

    const activeContent = $('.tab-content-wrapper.active');
    const activatedContent = $(`.tab-content-wrapper[data-tab-id=${tab.attr('id')}]`);

    activeTab.removeClass('active');
    tab.addClass('active').parents('.sidenav-tab').addClass('active');
    activeContent.trigger('tab-deactivated').removeClass('active').slideUp();
    activatedContent.trigger('tab-activated').addClass('active').slideDown(
        () => activatedContent.trigger('tab-expanded')
    );
    addTabIDToURL(tab.attr('id'));
}

function addTabIDToURL(tabID) {
    const url = new URL(window.location.href);
    url.searchParams.set('tab', tabID);
    window.history.replaceState({}, '', url.href);
}
