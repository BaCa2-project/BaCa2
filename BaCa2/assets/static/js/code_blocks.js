function codeBlocksSetup() {
    codeBlockButtonsSetup();
}

function codeBlockButtonsSetup() {
    $(".line-numbers-btn").on("click", function() {
        const target = $(`#${$(this).data("target")}`);
        lineNumbersToggle(target);
    });

    $(".line-wrap-btn").on("click", function() {
        const target = $(`#${$(this).data("target")}`);
        lineWrapToggle(target);
    });
}

function lineNumbersToggle(codeBlock) {
    codeBlock.toggleClass('line-numbers');
    codeBlock.find('.line-numbers-rows').toggleClass('d-none');
}

function lineWrapToggle(codeBlock) {
    codeBlock.toggleClass('wrap-lines');
    Prism.highlightElement(codeBlock.find('code')[0]);
}
