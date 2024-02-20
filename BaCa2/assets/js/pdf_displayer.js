class PDFDisplayer {
    constructor(widgetId, pdfUrl) {
        this.pdfUrl = pdfUrl;
        this.pdfDoc = null;
        this.pageNum = 1;
        this.pageRendering = false;
        this.pageNumPending = null;
        this.scale = 2.5;
        this.displayer = $(`#${widgetId}`);
        this.canvas = this.displayer.find('canvas')[0];
        this.context = this.canvas.getContext('2d');
        this.init();
    }

    renderPage(num) {
        this.pageRendering = true;

        this.pdfDoc.getPage(num).then(page => {
            const viewport = page.getViewport({ scale: this.scale });
            this.canvas.height = viewport.height;
            this.canvas.width = viewport.width;

            const renderContext = {
                canvasContext: this.context,
                viewport: viewport
            };

            page.render(renderContext).promise.then(() => {
                this.pageRendering = false;

                if (this.pageNumPending !== null) {
                    this.renderPage(this.pageNumPending);
                    this.pageNumPending = null;
                }
            });

            this.displayer.find('.pdf-current-page').val(num);
        });
    }

    queueRenderPage(num) {
        if (this.pageRendering)
            this.pageNumPending = num;
        else
            this.renderPage(num);
    }

    showPrevPage() {
        if (this.pageNum <= 1)
            return;
        this.pageNum--;
        this.queueRenderPage(this.pageNum);
    }

    showNextPage() {
        if (this.pageNum >= this.pdfDoc.numPages)
            return;
        this.pageNum++;
        this.queueRenderPage(this.pageNum);
    }

    init() {
        pdfjsLib.getDocument(this.pdfUrl).promise.then(pdf => {
            this.pdfDoc = pdf;
            this.displayer.find('.pdf-page-count').text(this.pdfDoc.numPages);
            this.displayer.find('.prev-page-btn').on('click', () => this.showPrevPage());
            this.displayer.find('.next-page-btn').on('click', () => this.showNextPage());
            this.displayer.find('.pdf-page-change').submit(e => {
                e.preventDefault();
                const pageNum = parseInt(this.displayer.find('.pdf-page-number').val());
                if (pageNum > 0 && pageNum <= this.pdfDoc.numPages)
                    this.queueRenderPage(pageNum);
            });
            this.renderPage(this.pageNum);
        });
    }
}