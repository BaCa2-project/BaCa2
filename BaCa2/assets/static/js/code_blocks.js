$(document).ready(function () {
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

(function () {
    if (typeof Prism === 'undefined' || typeof document === 'undefined') {
        return;
    }

    if (!Prism.plugins.toolbar) {
        console.warn('Copy to Clipboard plugin loaded before Toolbar plugin.');
        return;
    }

    function getSettings(settings, startElement) {
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

    function lineNumbersToggle(code) {
        const codeBlock = code.closest('.code-block')
        codeBlock.toggleClass('line-numbers');
        const lineNumbers = codeBlock.find('.line-numbers-rows');

        if (lineNumbers.length === 0)
            Prism.highlightElement(code[0]);
        else
            lineNumbers.toggleClass('d-none');
    }

    function lineWrapToggle(code) {
        const codeBlock = code.closest('.code-block')
        codeBlock.toggleClass('wrap-lines');
        Prism.highlightElement(code[0]);
    }

    Prism.plugins.toolbar.registerButton('copy-to-clipboard', function (env) {
        const copySettings = {
            'copy': $('<i class="bi bi-copy"></i>'),
            'copy-error': $('<i class="bi bi-x-lg"></i>'),
            'copy-success': $('<i class="bi bi-check-lg"></i>'),
            'copy-timeout': 2500
        };

        const code = $(env.element)
        const settings = getSettings(copySettings, code);
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
                setTimeout(function () {
                    alert('Error copying text to clipboard, press Ctrl+C to copy');
                }, 100);
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

    Prism.plugins.toolbar.registerButton('select-code', function (env) {
        const selectSettings = {
            'select': $('<i class="bi bi-text-left"></i>'),
            'select-success': $('<i class="bi bi-check-lg"></i>'),
            'select-timeout': 2500
        };

        const code = $(env.element)
        const settings = getSettings(selectSettings, code);
        const selectBtn = $('<button class="select-code-button" type="button"></button>');
        const selectSpan = $('<span></span>');

        selectBtn.addClass('btn btn-sm btn-outline-secondary');
        selectBtn.append(selectSpan);
        setState('select');

        selectBtn.on('click', function () {
            selectElementText(code[0]);
            setState('select-success');
            resetText();
        });

        return selectBtn[0];

        function resetText() {
            setTimeout(function () {
                setState('select');
            }, settings['select-timeout']);
        }

        function setState(state) {
            selectSpan.html(settings[state]);
            selectSpan.attr('data-select-state', state);
        }
    });

    Prism.plugins.toolbar.registerButton('line-numbers', function (env) {
        const lineNumbersSettings = {
            'line-numbers': $('<i class="bi bi-list-ul"></i>'),
            'line-numbers-hidden': $('<i class="bi bi-list-ol"></i>')
        };

        const code = $(env.element)
        const settings = getSettings(lineNumbersSettings, code);
        const lineNumbersBtn = $('<button class="line-numbers-btn" type="button"></button>');
        const lineNumbersSpan = $('<span></span>');

        lineNumbersBtn.addClass('btn btn-sm btn-outline-secondary');
        lineNumbersBtn.append(lineNumbersSpan);
        setInitialState();

        lineNumbersBtn.on('click', function () {
            lineNumbersToggle(code);
            switchState();
        });

        return lineNumbersBtn[0];

        function setInitialState() {
            const codeBlock = code.closest('.code-block')

            if (codeBlock.hasClass('line-numbers'))
                setState('line-numbers');
            else
                setState('line-numbers-hidden');
        }

        function switchState() {
            if (lineNumbersSpan.attr('data-line-numbers-state') === 'line-numbers')
                setState('line-numbers-hidden');
            else
                setState('line-numbers');
        }

        function setState(state) {
            lineNumbersSpan.html(settings[state]);
            lineNumbersSpan.attr('data-line-numbers-state', state);
        }
    });

    Prism.plugins.toolbar.registerButton('line-wrap', function (env) {
        const lineWrapSettings = {
            'line-wrap': $('<i class="bi bi-text-wrap"></i>'),
            'line-nowrap': $('<i class="bi bi-text-wrap"></i>')
        };

        const code = $(env.element)
        const settings = getSettings(lineWrapSettings, code);
        const lineWrapBtn = $('<button class="line-wrap-btn" type="button"></button>');
        const lineWrapSpan = $('<span></span>');

        lineWrapBtn.addClass('btn btn-sm btn-outline-secondary');
        lineWrapBtn.append(lineWrapSpan);
        setInitialState();

        lineWrapBtn.on('click', function () {
            lineWrapToggle(code);
            switchState();
        });

        return lineWrapBtn[0];

        function setInitialState() {
            const codeBlock = code.closest('.code-block')

            if (codeBlock.hasClass('wrap-lines'))
                setState('line-wrap');
            else
                setState('line-nowrap');
        }

        function switchState() {
            if (lineWrapSpan.attr('data-line-wrap-state') === 'line-wrap')
                setState('line-nowrap');
            else
                setState('line-wrap');
        }

        function setState(state) {
            lineWrapSpan.html(settings[state]);
            lineWrapSpan.attr('data-line-wrap-state', state);
        }
    });
}());
