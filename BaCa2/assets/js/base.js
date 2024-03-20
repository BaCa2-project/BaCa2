function preInitCommon() {
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

function showPage() {
    $(".main-container").show();
}

function generateFormattedString(data, formatString) {
    return formatString.replace(/\[\[(\w+)]]/g, function (match, key) {
       return data[key] || match;
    });
}
