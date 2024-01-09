function transformLoginFormBtn(loginFormBtn, text, cls, loginForm) {
    loginFormBtn.position("relative");
    loginFormBtn.text(text);
    loginFormBtn.attr("class", cls);
    loginFormBtn.click(() => loginForm.submit());
}

function initLoginPage() {
    const loginForm = $("#login_form");
    const loginBtn = loginForm.find("button");
    const loginFormBtn = $("#login-form-btn");
    const alert = $(".alert-danger");

    if (!sessionStorage.getItem("loginFormRefresh")) {
        loginForm.hide();
        loginBtn.hide();
        loginFormBtn.css("transition", "all 0.8s ease");
        loginFormBtn.click(() => {
            $("#login_form").slideDown("slow", () => loginForm.find("#username").focus());
            transformLoginFormBtn(loginFormBtn, loginBtn.text(), loginBtn.attr("class"), loginForm);
            shrinkLogo($(".logo-wrapper"));
        });
    }
    else {
        loginBtn.hide();
        shrinkLogo($(".logo-wrapper"), false);
        transformLoginFormBtn(loginFormBtn, loginBtn.text(), loginBtn.attr("class"), loginForm);

        if (!sessionStorage.getItem("loginFormAlert"))
            alert.hide();
    }

    sessionStorage.removeItem("loginFormRefresh");

    $(document).on("submit", "#login_form",
        (e) => sessionStorage.setItem("loginFormRefresh", "true"))
}

function displayLoginFormAlert() {
    const alert = $(".alert-danger");

    if (!sessionStorage.getItem("loginFormAlert"))
            alert.slideDown("slow");

    if (alert.length > 0)
        sessionStorage.setItem("loginFormAlert", "true");
    else
        sessionStorage.removeItem("loginFormAlert");
}