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

$(document).ready(function() {
    codeBlockButtonsSetup();

    $('.tab-content-wrapper').each(function() {
        const codeBlocks = $(this).find('.code-block');
        const lineNumbers = codeBlocks.find('.line-numbers-rows');

        if (lineNumbers.length === 0)
            return;

        if (!$(this).hasClass('active'))
            codeBlocks.addClass('line-numbers-hidden');

        $(this).one('tab-expanded', function() {
            codeBlocks.each(function() {
                Prism.plugins.lineNumbers && Prism.plugins.lineNumbers.resize(this);
            });

            codeBlocks.removeClass('line-numbers-hidden');
        });
    });
});

Prism.plugins.toolbar.registerButton('select-code', function(env) {
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

	function registerClipboard(element, copyInfo) {
		element.addEventListener('click', function () {
			copyTextToClipboard(copyInfo);
		});
	}

	function copyTextToClipboard(copyInfo) {
		if (navigator.clipboard) {
			navigator.clipboard.writeText(copyInfo.getText()).then(() => {

            }).catch(() => {

            });
		} else {

		}
	}

	function selectElementText(element) {
		window.getSelection().selectAllChildren(element);
	}

	function getSettings(startElement) {
        const settings = {
            'copy': 'Copy',
            'copy-error': 'Press Ctrl+C to copy',
            'copy-success': 'Copied!',
            'copy-timeout': 5000
        };

        const prefix = 'data-prismjs-';
        for (const key in settings) {
            const attr = prefix + key;
            let element = startElement;
            while (element && !element.hasAttribute(attr)) {
				element = element.parentElement;
			}
			if (element) {
				settings[key] = element.getAttribute(attr);
			}
		}
		return settings;
	}

	Prism.plugins.toolbar.registerButton('copy-to-clipboard', function (env) {
        const element = env.element;

        const settings = getSettings(element);

        const linkCopy = document.createElement('button');
        linkCopy.className = 'copy-to-clipboard-button';
		linkCopy.setAttribute('type', 'button');
        const linkSpan = document.createElement('span');
        linkCopy.appendChild(linkSpan);

		setState('copy');

		registerClipboard(linkCopy, {
			getText: function () {
				return element.textContent;
			},
			success: function () {
				setState('copy-success');

				resetText();
			},
			error: function () {
				setState('copy-error');

				setTimeout(function () {
					selectElementText(element);
				}, 1);

				resetText();
			}
		});

		return linkCopy;

		function resetText() {
			setTimeout(function () { setState('copy'); }, settings['copy-timeout']);
		}

		function setState(state) {
			linkSpan.textContent = settings[state];
			linkCopy.setAttribute('data-copy-state', state);
		}
	});
}());
