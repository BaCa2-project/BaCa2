function shrinkLogo(logoWrapper) {
    if (logoWrapper.hasClass("logo-l"))
        logoWrapper.removeClass("logo-l").addClass("logo-m");
    else if (logoWrapper.hasClass("logo-m"))
        logoWrapper.removeClass("logo-m").addClass("logo-s");
    else if (logoWrapper.hasClass("logo-s"))
        logoWrapper.removeClass("logo-s").addClass("logo-xs");
}