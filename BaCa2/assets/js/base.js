function preInitCommon() {
    formsPreSetup();
    tablesPreSetup();
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
}

function showPage() {
    $(".main-container").show();
}

function generateFormattedString(data, formatString) {
    return formatString.replace(/\[\[(\w+)]]/g, function (match, key) {
       return data[key] || match;
    });
}
