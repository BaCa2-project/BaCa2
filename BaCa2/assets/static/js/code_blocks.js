function codeBlockButtonsSetup() {
    $(".line-numbers-btn").on("click", function () {
        const target = $(`#${$(this).data("target")}`);
        lineNumbersToggle(target);
    });

    $(".line-wrap-btn").on("click", function () {
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

$(document).ready(function () {
    codeBlockButtonsSetup();

    $('.tab-content-wrapper').each(function () {
        const codeBlocks = $(this).find('.code-block');
        const lineNumbers = codeBlocks.find('.line-numbers-rows');

        if (lineNumbers.length === 0)
            return;

        if (!$(this).hasClass('active'))
            codeBlocks.addClass('line-numbers-hidden');

        $(this).one('tab-expanded', function () {
            codeBlocks.each(function () {
                Prism.plugins.lineNumbers && Prism.plugins.lineNumbers.resize(this);
            });

            codeBlocks.removeClass('line-numbers-hidden');
        });
    });
});

Prism.plugins.toolbar.registerButton('select-code', function (env) {
    const button = document.createElement('button');
    button.innerHTML = 'Select Code';

    button.addEventListener('click', function () {
        // Source: http://stackoverflow.com/a/11128179/2757940
        if (document.body.createTextRange) { // ms
            var range = document.body.createTextRange();
            range.moveToElementText(env.element);
            range.select();
        } else if (window.getSelection) { // moz, opera, webkit
            var selection = window.getSelection();
            var range = document.createRange();
            range.selectNodeContents(env.element);
            selection.removeAllRanges();
            selection.addRange(range);
        }
    });

    $(button).addClass('btn btn-sm btn-outline-secondary');

    return button;
});

(function () {
    if (typeof Prism === 'undefined' || typeof document === 'undefined') {
        return;
    }

    if (!Prism.plugins.toolbar) {
        console.warn('Copy to Clipboard plugin loaded before Toolbar plugin.');
        return;
    }

    function registerClipboard(copyBtn, copyInfo) {
        copyBtn.on('click', function () {
            if (navigator.clipboard)
                navigator.clipboard.writeText(copyInfo.getText())
                         .then(copyInfo.success, copyInfo.error);
            else
                copyInfo.error();
        });
    }

    function selectElementText(element) {
        window.getSelection().selectAllChildren(element);
    }

    function getSettings(startElement) {
        const settings = {
            'copy': $('<i class="bi bi-clipboard"></i>'),
            'copy-error': 'Press Ctrl+C to copy',
            'copy-success': $('<i class="bi bi-clipboard-check"></i>'),
            'copy-timeout': 5000
        };

        const prefix = 'data-prismjs-';

        for (const key in settings) {
            const attr = prefix + key;
            let element = startElement;

            while (element.parent().length > 0 && element.attr(attr) === undefined)
                element = element.parent();

            if (element.attr(attr) !== undefined)
                settings[key] = element.attr(attr);
        }

        return settings;
    }

    Prism.plugins.toolbar.registerButton('copy-to-clipboard', function (env) {
        const code = $(env.element)
        const settings = getSettings(code);
        const copyBtn = $('<button class="copy-to-clipboard-button" type="button"></button>');
        const copySpan = $('<span></span>');

        copyBtn.addClass('btn btn-sm btn-outline-secondary');
        copyBtn.append(copySpan);
        setState('copy');

        registerClipboard(copyBtn, {
            getText: function () {
                return code.text();
            },

            success: function () {
                setState('copy-success');
                resetText();
            },

            error: function () {
                setState('copy-error');
                setTimeout(function () {
                    selectElementText(code[0]);
                }, 1);
                resetText();
            }
        });

        return copyBtn[0];

        function resetText() {
            setTimeout(function () {
                setState('copy');
            }, settings['copy-timeout']);
        }

        function setState(state) {
            copySpan.html(settings[state]);
            copySpan.attr('data-copy-state', state);
        }
    });
}());
