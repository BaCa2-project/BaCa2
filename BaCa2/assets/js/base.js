function preInitCommon() {
    ajaxErrorHandlingSetup();
    formsPreSetup();
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
    themeSetup();
}

function ajaxErrorHandlingSetup() {
    $(document).ajaxError(function (event, jqxhr, settings, thrownError) {
        if (jqxhr.status === 401) {
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
