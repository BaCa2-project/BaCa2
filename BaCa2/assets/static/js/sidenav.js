function sidenavSetup() {
    $('.sidenav-tab:not(.has-sub-tabs)').click(function () {
        const sidenav = $(this).closest('.sidenav');
        const activeTab = sidenav.find('.sidenav-tab.active');
        const activatedTab = $(this);

        if (activeTab[0] === activatedTab[0])
            return;

        const activeContent = $('.tab-content-wrapper.active');
        const activatedContent = $(`.tab-content-wrapper[data-tab-id=${$(this).attr('id')}]`);


        activeTab.removeClass('active');
        activatedTab.addClass('active').parents('.sidenav-tab').addClass('active');
        activeContent.trigger('tab-deactivated').removeClass('active').slideUp();
        activatedContent.trigger('tab-activated').addClass('active').slideDown();
    });
}
