function initCommon() {
    if (!window.location.href.includes("login")) {
        sessionStorage.removeItem("loginFormRefresh");
        sessionStorage.removeItem("loginFormAlert");
    }
    buttonsSetup();
    formsSetup();
}

function showPage() {
    $(".main-container").show();
}
