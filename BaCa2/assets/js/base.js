function initCommon() {
    if (!window.location.href.includes("login")) {
        sessionStorage.removeItem("loginFormRefresh");
        sessionStorage.removeItem("loginFormAlert");
    }
}

function showPage() {
    $(".main-container").show();
}
