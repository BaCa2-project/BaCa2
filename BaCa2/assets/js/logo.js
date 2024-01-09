function shrinkLogo(logoWrapper, animated = true) {
    const prevTransition = logoWrapper.find("baca2-logo").css("transition");

    if (!animated)
        logoWrapper.find("baca2-logo").css("transition", "none");

    if (logoWrapper.hasClass("logo-l"))
        logoWrapper.removeClass("logo-l").addClass("logo-m");
    else if (logoWrapper.hasClass("logo-m"))
        logoWrapper.removeClass("logo-m").addClass("logo-s");
    else if (logoWrapper.hasClass("logo-s"))
        logoWrapper.removeClass("logo-s").addClass("logo-xs");

    if (!animated)
        logoWrapper.find("baca2-logo").css("transition", prevTransition);
}