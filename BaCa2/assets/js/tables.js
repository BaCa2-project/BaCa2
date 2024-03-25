// ------------------------------------ table widget class ------------------------------------ //

class TableWidget {
    constructor(tableId, DTObj, ajax) {
        this.DTObj = DTObj;
        this.table = $(`#${tableId}`);
        this.ajax = ajax;
        this.widgetWrapper = this.table.closest('.table-wrapper');
        this.lastSelectedRow = null;
        this.lastDeselectedRow = null;
    }

    // -------------------------------- record select methods --------------------------------- //

    toggleSelectRow(row, on) {
        if (on) {
            this.lastSelectedRow = row;
            this.lastDeselectedRow = null;
            row.addClass('row-selected');
        } else {
            this.lastSelectedRow = null;
            this.lastDeselectedRow = row;
            row.removeClass('row-selected');
        }
    }

    toggleSelectRows(rows, on) {
        rows.each(function () {
            $(this).find('.select-checkbox').prop('checked', on);

            if (on)
                $(this).addClass('row-selected');
            else
                $(this).removeClass('row-selected');
        });
    }

    toggleSelectRange(row, on) {
        const rows = this.getRowsInOrder();
        const currentIndex = this.getRowIndex(row)
        const lastIndex = on ?
                          this.getRowIndex(this.lastSelectedRow) :
                          this.getRowIndex(this.lastDeselectedRow);

        let selecting = false;
        let last = false;

        for (let i = 0; i < rows.length; i++) {
            const row = rows[i];
            const index = this.getRowIndex(row);

            if (index === currentIndex || index === lastIndex) {
                if (selecting)
                    last = true;
                else
                    selecting = true;
            }

            if (selecting) {
                if (on)
                    $(row).addClass('row-selected');
                else
                    $(row).removeClass('row-selected');
                $(row).find('.select-checkbox').prop('checked', on);
            }

            if (last)
                break;
        }
    }

    toggleSelectAll(on) {
        this.getCurrentRowsInOrder().each(function () {
            $(this).find('.select-checkbox').prop('checked', on);

            if (on)
                $(this).addClass('row-selected');
            else
                $(this).removeClass('row-selected');
        });
    }

    updateSelectHeader() {
        const headerCheckbox = this.widgetWrapper.find('.select-header-checkbox');
        let allSelected = true;
        let noneSelected = true;
        let rows = this.getCurrentPageRowsInOrder();

        if (this.table.hasClass('filtered'))
            rows = this.getCurrentRowsInOrder();

        rows.each(function () {
            if ($(this).hasClass('row-selected'))
                noneSelected = false;
            else
                allSelected = false;
        });

        if (noneSelected) {
            headerCheckbox.prop('checked', false);
            headerCheckbox.prop('indeterminate', false);
            headerCheckbox.data('state', 'off');
        } else if (allSelected) {
            headerCheckbox.prop('checked', true);
            headerCheckbox.prop('indeterminate', false);
            headerCheckbox.data('state', 'on');
        } else {
            headerCheckbox.prop('checked', false);
            headerCheckbox.prop('indeterminate', true);
            headerCheckbox.data('state', 'indeterminate');
        }
    }

    // ------------------------------------ getter methods ------------------------------------ //

    getRowsInOrder() {
        return this.DTObj.rows({order: 'applied'}).nodes().to$();
    }

    getCurrentPageRowsInOrder() {
        return this.DTObj.rows({order: 'applied', page: 'current'}).nodes().to$();
    }

    getCurrentRowsInOrder() {
        return this.DTObj
                   .rows({order: 'applied', page: 'current', search: 'applied'})
                   .nodes().to$();
    }

    getAllSelectedRows() {
        return this.DTObj.rows().nodes().to$().filter(function () {
            return $(this).hasClass('row-selected');
        });
    }

    getFilteredOutRows() {
        return this.DTObj.rows({search: 'removed'}).nodes().to$();
    }

    getRowIndex(row) {
        return this.DTObj.row(row).index();
    }

    // ----------------------------------- row check methods ---------------------------------- //

    hasLastSelectedRow() {
        return this.lastSelectedRow !== null;
    }

    hasLastDeselectedRow() {
        return this.lastDeselectedRow !== null;
    }
}


// --------------------------------------- tables setup --------------------------------------- //

function tablesPreSetup() {
    tableResizeSetup();

    $(document).on('tab-activated', function (e) {
        const tab = $(e.target);
        const tableId = tab.find('.table-wrapper').data('table-id');

        if (tableId === undefined)
            return;

        const tableWidget = window.tableWidgets[`#${tableId}`];

        if (!tableWidget.ajax)
            return;

        tableWidget.DTObj.ajax.reload(function () {
            tableWidget.DTObj.columns.adjust().draw();
            $(`#${tableId}`).trigger('table-reload');
        });
    });
}

function tablesSetup() {
    $('.delete-record-form').each(function () {
        deleteRecordFormSetup($(this).find('form'), $(this).data('table-id'));
    });

    $('.table-refresh-btn').on('click', function () {
        refreshButtonClickHandler($(this));
    });

    $('.table-wrapper').each(function () {
        const tableId = $(this).data('table-id');

        $(this).find('th.select').each(function () {
            renderSelectHeader($(this), tableId);
        });

        globalSearchSetup($(this));
        columnSearchSetup($(this));
    });

    $('.link-records').each(function () {
        recordLinkSetup($(this).attr('id'));
    });

    lengthMenuSetup();
}


// --------------------------------------- table search --------------------------------------- //

function globalSearchSetup(tableWrapper) {
    const search = tableWrapper.find('.dataTables_filter');

    if (search.length === 0)
        return;

    const searchInput = search.find('input');
    const searchWrapper = tableWrapper.find('.table-util-header .table-search');
    const tableId = tableWrapper.data('table-id');
    const table = tableWrapper.find(`#${tableId}`);
    const tableWidget = window.tableWidgets[`#${tableId}`];

    searchInput.addClass('form-control').attr('placeholder', 'Search').attr('type', 'text');
    searchInput.attr('id', `${tableId}_search`);
    searchInput.on('input', function () {
        globalSearchInputHandler($(this), table, tableWidget);
    });
    searchWrapper.append(searchInput);
    search.remove();
}


function globalSearchInputHandler(inputField, table, tableWidget) {
    if (table.data('deselect-on-filter'))
        tableWidget.toggleSelectRows(tableWidget.getFilteredOutRows(), false);

    if (inputField.val() === '')
        table.removeClass('filtered');
    else
        table.addClass('filtered');

    tableWidget.updateSelectHeader();
}


function columnSearchSetup(tableWrapper) {
    const tableId = tableWrapper.data('table-id');
    const table = tableWrapper.find(`#${tableId}`);
    const tableWidget = window.tableWidgets[`#${table.attr('id')}`]

    tableWrapper.find('.column-search').on('click', function (e) {
        e.stopPropagation();
    }).on('input', function () {
        columnSearchInputHandler($(this), table, tableWidget)
    });
}


function columnSearchInputHandler(inputField, table, tableWidget) {
    tableWidget.DTObj.column(inputField.closest('th')).search(inputField.val()).draw();

    if (table.data('deselect-on-filter'))
        tableWidget.toggleSelectRows(tableWidget.getFilteredOutRows(), false);

    if (inputField.val() === '')
        table.removeClass('filtered');
    else
        table.addClass('filtered');

    tableWidget.updateSelectHeader();
}


// ---------------------------------------- length menu --------------------------------------- //

function lengthMenuSetup() {
    $('.dataTables_length').each(function () {
        const label = $(this).find('label');
        label.addClass('d-flex align-items-center');

        const select = $(this).find('select');
        select.addClass('form-select form-select-fm auto-width ms-2 me-2');
    });
}


// --------------------------------------- table buttons -------------------------------------- //

function refreshButtonClickHandler(button) {
    const tableId = button.data('refresh-target');
    const tableWidget = window.tableWidgets[`#${tableId}`];
    tableWidget.DTObj.ajax.reload(function () {
        tableWidget.DTObj.columns.adjust().draw();
        tableWidget.updateSelectHeader();
        $(`#${tableId}`).trigger('table-reload');
    });
}


// ---------------------------------------- table forms --------------------------------------- //

function deleteRecordFormSetup(form, tableId) {
    form.on('submit-success', function (e, data) {
        window.tableWidgets[`#${tableId}`].DTObj.ajax.reload();
    });
}


function recordLinkSetup(tableId) {
    $(`#${tableId}`).on('click', 'tbody tr[data-record-link]', function () {
        window.location.href = $(this).data('record-link');
    });
}


// -------------------------------------- DataTables init ------------------------------------- //

function initTable(
    {
        tableId,
        ajax,
        dataSourceUrl,
        dataSource,
        linkFormatString,
        cols,
        defaultSorting,
        defaultOrder,
        defaultOrderCol,
        searching,
        paging,
        limitHeight,
        height,
        refresh,
        refreshInterval,
        localisation_cdn,
    } = {}
) {
    const tableParams = {};
    const table = $(`#${tableId}`);

    if (ajax)
        tableParams['ajax'] = dataSourceUrl;
    else
        tableParams['data'] = dataSource;

    if (defaultSorting)
        tableParams['order'] = [[defaultOrderCol, defaultOrder]];
    else
        tableParams['order'] = [];

    if (limitHeight) {
        tableParams['scrollResize'] = true;
        tableParams['scrollY'] = height;
        tableParams['scrollCollapse'] = true;
    }

    if (localisation_cdn){
        tableParams['language'] = {
            "url": localisation_cdn
        }
    }

    tableParams['searching'] = searching;

    const columns = [];
    cols.forEach(col => {
        columns.push({'data': col['name']})
    });
    tableParams['columns'] = columns;

    const columnDefs = [];
    cols.forEach(col => columnDefs.push(createColumnDef(col, cols.indexOf(col))));
    tableParams['columnDefs'] = columnDefs;

    tableParams['rowCallback'] = createRowCallback(linkFormatString);

    createPagingDef(paging, tableParams, table, tableId);

    if (!window.tableWidgets)
        window.tableWidgets = {};

    window.tableWidgets[`#${tableId}`] = new TableWidget(
        tableId,
        table.DataTable(tableParams),
        ajax
    );

    if (refresh)
        setRefresh(tableId, refreshInterval);
}


function createPagingDef(paging, DTParams, table, tableId) {
    if (paging) {
        DTParams['pageLength'] = paging['page_length'];

        if (JSON.parse(paging['allow_length_change'])) {
            const pagingMenuVals = [];
            const pagingMenuLabels = [];

            paging['length_change_options'].forEach(option => {
                pagingMenuVals.push(option);
                pagingMenuLabels.push(option === -1 ? 'All' : `${option}`);
            })

            DTParams['lengthMenu'] = [pagingMenuVals, pagingMenuLabels];
        } else
            DTParams['lengthChange'] = false;

        if (JSON.parse(paging['deselect_on_page_change'])) {
            const tableWrapper = table.closest('.table-wrapper');

            table.on('page.dt', function () {
                const selectHeaderCheckbox = tableWrapper.find('th .select-header-checkbox');
                window.tableWidgets[`#${tableId}`].toggleSelectAll(false);
                selectHeaderCheckbox.prop('checked', false);
                selectHeaderCheckbox.prop('indeterminate', false);
            });
        }
    } else
        DTParams['paging'] = false;
}


function setRefresh(tableId, interval) {
    setInterval(function () {
        window.tableWidgets[`#${tableId}`].DTObj.ajax.reload();
    }, interval);
}


function createRowCallback(linkFormatString) {
    return function (row, data) {
        $(row).attr('data-record-id', `${data.id}`);
        $(row).attr('data-record-data', JSON.stringify(data));

        if (linkFormatString) {
            $(row).attr('data-record-link', generateFormattedString(data, linkFormatString));
        }
    }
}


function createColumnDef(col, index) {
    const def = {
        'targets': [index],
        'orderable': JSON.parse(col['sortable']),
        'searchable': JSON.parse(col['searchable']),
        'className': col['col_type']
    };

    if (JSON.parse(col['data_null']))
        def['data'] = null;

    if (!JSON.parse(col['auto_width'])) {
        def['autoWidth'] = false;
        def['width'] = col['width'];
    } else
        def['autoWidth'] = true;

    switch (col['col_type']) {
        case 'select':
            def['render'] = renderSelectField;
            break;
        case 'delete':
            def['render'] = renderDeleteField;
            break;
        case 'datetime':
            def['render'] = DataTable.render.datetime(col['formatter']);
            break;
        case 'form_submit':
            def['render'] = renderFormSubmitField(col);
            break;
    }

    return def;
}


// ------------------------------- special field render methods ------------------------------- //

function renderSelectField(data, type, row, meta) {
    return $('<input>')
        .attr('type', 'checkbox')
        .attr('class', 'form-check-input select-checkbox')
        .attr('data-record-target', row['id'])
        .attr('onclick', 'selectCheckboxClickHandler(event, $(this))')
        [0].outerHTML;
}


function renderSelectHeader(header, tableId) {
    const checkbox = $('<input>')
        .attr('type', 'checkbox')
        .attr('class', 'form-check-input select-header-checkbox')
        .attr('data-state', 'off')
        .on('click', function () {
            selectHeaderClickHandler($(this), tableId);
        });
    header.append(checkbox);
}


function renderDeleteField(data, type, row, meta) {
    return $('<a>')
        .attr('href', '#')
        .attr('data-record-target', row['id'])
        .attr('onclick', 'deleteButtonClickHandler(event, $(this))')
        .html('<i class="bi bi-x-lg"></i>')
        [0].outerHTML;
}

function renderFormSubmitField(col) {
    const mappings = col['mappings'];
    const form_id = col['form_id'];
    const btnIcon = col['btn_icon'];
    const btnText = col['btn_text'];

    return function (data, type, row, meta) {
        const button = $('<a>')
            .attr('class', 'btn btn-outline-primary')
            .attr('href', '#')
            .attr('data-mappings', mappings)
            .attr('data-form-id', form_id)
            .attr('onclick', 'formSubmitButtonClickHandler(event, $(this))');

        const content = $('<div>').addClass('d-flex');

        if (btnIcon) {
            const icon = $('<i>').addClass(`bi bi-${btnIcon}`).addClass(btnText ? 'me-2' : '');
            content.append(icon);
        }

        content.append(btnText);
        button.append(content);
        return button[0].outerHTML;
    };
}


// ------------------------------- special field click handlers ------------------------------- //

function selectHeaderClickHandler(checkbox, tableId) {
    const table = checkbox.closest('.table-wrapper').find(`#${tableId}`);
    const tableWidget = window.tableWidgets[`#${tableId}`];

    tableWidget.toggleSelectAll(
        checkbox.prop('checked')
    );

    if (table.hasClass('filtered')) {
        tableWidget.updateSelectHeader();
    }
}


function selectCheckboxClickHandler(e, checkbox) {
    e.stopPropagation();
    const table = window.tableWidgets[`#${checkbox.closest('table').attr('id')}`]
    const row = checkbox.closest('tr');
    const on = checkbox.prop('checked');

    if (e.shiftKey && on && table.hasLastSelectedRow())
        table.toggleSelectRange(row, on);
    else if (e.ctrlKey && !on && table.hasLastDeselectedRow())
        table.toggleSelectRange(row, on);
    else
        table.toggleSelectRow(row, on);

    table.updateSelectHeader();
}


function deleteButtonClickHandler(e, button) {
    e.stopPropagation();
    const form = button.closest('.table-wrapper').find('.delete-record-form form');
    const input = form.find('input').filter(function () {
        return $(this).hasClass('model-id')
    });
    input.val(button.data('record-target'));
    form.find('.submit-btn')[0].click();
}


function formSubmitButtonClickHandler(e, button) {
    e.stopPropagation();
    const mappings = button.data('mappings');
    const formId = button.data('form-id');
    const form = $(`#${formId}`);
    const data = button.closest('tr').data('record-data');

    for (const key in mappings) {
        const input = form.find(`input[name="${key}"]`);
        input.val(data[mappings[key]]);
    }

    form.find('.submit-btn')[0].click();
}


// -------------------------------------- resizable table ------------------------------------- //

function tableResizeSetup() {
    $(document).on('init.dt', function (e) {
        const table = $(e.target);
        const resizeWrapper = table.closest('.resize-wrapper');

        if (!resizeWrapper.length) return;

        const DTLength = resizeWrapper.find('.dataTables_length');
        const DTInfo = resizeWrapper.find('.dataTables_info');
        const DTPaging = resizeWrapper.find('.dataTables_paginate');

        const lengthSelect = $('<div>').addClass('dataTables_wrapper mb-1');
        lengthSelect.append(DTLength);
        lengthSelect.insertBefore(resizeWrapper);

        const pagingInfo = $('<div>').addClass('dataTables_wrapper mb-1')
        pagingInfo.append(DTInfo);
        pagingInfo.append(DTPaging);
        pagingInfo.insertAfter(resizeWrapper);

        const DTScroll = resizeWrapper.find('.dataTables_scroll');
        const DTScrollHead = DTScroll.find('.dataTables_scrollHead');
        const DTScrollBody = DTScroll.find('.dataTables_scrollBody');

        const bodyHeight = DTScroll.height() - DTScrollHead.height();

        DTScrollBody.height(bodyHeight);
        DTScrollBody.css('max-height', bodyHeight);

        const resizeHandle = $(this).find('.resize-handle');
        const rowHeight = table.find('tbody tr').first().height();

        resizeHandle.on('mousedown', function (e) {
            e.preventDefault();
            const startY = e.pageY;
            const startHeight = resizeWrapper.height();


            $(document).on('mousemove', function (e) {
                e.preventDefault();
                let newHeight = startHeight + e.pageY - startY;
                let newBodyHeight = newHeight - DTScrollHead.height();

                if (newBodyHeight < rowHeight) {
                    newBodyHeight = rowHeight;
                    newHeight = newBodyHeight + DTScrollHead.height();
                }

                if (newBodyHeight > table.height()) {
                    newBodyHeight = table.height();
                    newHeight = newBodyHeight + DTScrollHead.height();
                }

                resizeWrapper.height(newHeight);
                DTScrollBody.height(newBodyHeight);
                DTScrollBody.css('max-height', newBodyHeight);
            }).on('mouseup', function () {
                $(document).off('mousemove mouseup');
            });
        });
    });
}
