function preInitCommon() {
    scrollbarSetup();
    ajaxErrorHandlingSetup();
    tablesPreSetup();
    themePreSetup();
}

function initCommon() {
    if (!window.location.href.includes("login")) {
        sessionStorage.removeItem("loginFormRefresh");
        sessionStorage.removeItem("loginFormAlert");
    }
    buttonsSetup();
    tablesSetup();
    formsSetup();
    sideNavSetup();
    sidenavSetup();
    themeSetup();
}

function ajaxErrorHandlingSetup() {
    $(document).ajaxError(function (event, jqxhr, settings, thrownError) {
        if (jqxhr.status === 403) {
            location.reload();
        }
    });
}

function showPage() {
    $(".main-container").show();
}

function generateFormattedString(data, formatString) {
    return formatString.replace(/\[\[(\w+)]]/g, function (match, key) {
        return data[key].toString() || match;
    });
}

function scrollbarSetup() {
    $(document).ready(function () {
        const {OverlayScrollbars} = OverlayScrollbarsGlobal;

        OverlayScrollbars(document.body, {
            scrollbars: {
                theme: 'os-theme-dark os-theme-body',
                dragScroll: true
            }
        });

        $('.scrollable').each(function () {
            OverlayScrollbars(this, {
                scrollbars: {
                    theme: 'os-theme-dark os-theme-scrollable',
                    dragScroll: true
                }
            });
        });

        $('.dataTables_scrollBody').each(function () {
            OverlayScrollbars(this, {
                scrollbars: {
                    theme: 'os-theme-dark os-theme-table',
                    dragScroll: true
                }
            });
        });
    });
}
