function initCommon() {
    if (!window.location.href.includes("login")) {
        sessionStorage.removeItem("loginFormRefresh");
        sessionStorage.removeItem("loginFormAlert");
    }
    buttonsSetup();
    tablesSetup();
    formsSetup();
}

function showPage() {
    $(".main-container").show();
}
