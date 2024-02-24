// ------------------------------------ table widget class ------------------------------------ //

class TableWidget {
    constructor(tableId, table) {
        this.tableId = tableId;
        this.table = table;
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
        const table = $(`#${this.tableId}`);
        const headerCheckbox = table.find('.select-header-checkbox');
        let allSelected = true;
        let noneSelected = true;
        let rows = this.getRowsInOrder();

        if (table.hasClass('filtered'))
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
        return this.table
                   .rows({order: 'applied'})
                   .nodes().to$();
    }

    getCurrentRowsInOrder() {
        return this.table
                   .rows({order: 'applied', page: 'current', search: 'applied'})
                   .nodes().to$();
    }

    getCurrentSelectedRows() {
        return this.getCurrentRowsInOrder().filter(function () {
            return $(this).hasClass('row-selected');
        });
    }

    getAllSelectedRows() {
        return this.table.rows().nodes().to$().filter(function () {
            return $(this).hasClass('row-selected');
        });
    }

    getFilteredOutRows() {
        return this.table
                   .rows({search: 'removed'})
                   .nodes().to$();
    }

    getRowIndex(row) {
        return this.table.row(row).index();
    }

    getColumnIndex(colHeader) {
        return this.table.column(colHeader).index();
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

function tablesSetup() {
    $('th.select').each(function () {
        renderSelectHeader($(this));
    });

    $('.delete-record-form').each(function () {
        deleteRecordFormSetup($(this).find('form'), $(this).data('table-id'));
    });

    $('.table-refresh-btn').on('click', function () {
        refreshButtonClickHandler($(this));
    });

    $('.table-wrapper').each(function () {
        globalSearchSetup($(this));
        columnSearchSetup($(this));
    });

    $('.link-records').each(function () {
        recordLinkSetup($(this).attr('id'));
    });
}


// --------------------------------------- table search --------------------------------------- //

function globalSearchSetup(tableWrapper) {
    const search = tableWrapper.find('.dataTables_filter');

    if (search.length === 0)
        return;

    const searchInput = search.find('input');
    const searchWrapper = tableWrapper.find('.table-util-header .table-search');
    const table = tableWrapper.find('table')
    const tableId = table.attr('id');
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
    const table = tableWrapper.find('table')
    const tableWidget = window.tableWidgets[`#${table.attr('id')}`]

    tableWrapper.find('.column-search').on('click', function (e) {
        e.stopPropagation();
    }).on('input', function () {
        columnSearchInputHandler($(this), table, tableWidget)
    });
}

function columnSearchInputHandler(inputField, table, tableWidget) {
    tableWidget.table.column(inputField.closest('th')).search(inputField.val()).draw();

    if (table.data('deselect-on-filter'))
        tableWidget.toggleSelectRows(tableWidget.getFilteredOutRows(), false);

    if (inputField.val() === '')
        table.removeClass('filtered');
    else
        table.addClass('filtered');

    tableWidget.updateSelectHeader();
}


// --------------------------------------- table buttons -------------------------------------- //

function refreshButtonClickHandler(button) {
    const tableId = button.data('refresh-target');
    window.tableWidgets[`#${tableId}`].table.ajax.reload();
}


// ---------------------------------------- table forms --------------------------------------- //

function deleteRecordFormSetup(form, tableId) {
    form.on('submit-success', function (e, data) {
        window.tableWidgets[`#${tableId}`].table.ajax.reload();
    });
}

function recordLinkSetup(tableId) {
    $(`#${tableId}`).on('click', 'tbody tr', function () {
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
        tableParams['scrollY'] = height;
        tableParams['scrollCollapse'] = true;
    }

    tableParams['searching'] = searching;

    const columns = [];
    cols.forEach(col => {
        columns.push({'data': col['name']})
    });
    tableParams['columns'] = columns;

    if (paging) {
        tableParams['pageLength'] = paging['page_length'];

        if (JSON.parse(paging['allow_length_change'])) {
            const pagingMenuVals = [];
            const pagingMenuLabels = [];

            paging['length_change_options'].forEach(option => {
                pagingMenuVals.push(option);
                pagingMenuLabels.push(option === -1 ? 'All' : `${option}`);
            })

            tableParams['lengthMenu'] = [pagingMenuVals, pagingMenuLabels];
        } else
            tableParams['lengthChange'] = false;

        if (JSON.parse(paging['deselect_on_page_change']))
            table.on('page.dt', function () {
                const selectHeaderCheckbox = $(`#${tableId}`).find('th .select-header-checkbox');
                window.tableWidgets[`#${tableId}`].toggleSelectAll(false);
                selectHeaderCheckbox.prop('checked', false);
                selectHeaderCheckbox.prop('indeterminate', false);
            });
    } else
        tableParams['paging'] = false;

    const columnDefs = [];
    cols.forEach(col => columnDefs.push(createColumnDef(col, cols.indexOf(col))));
    tableParams['columnDefs'] = columnDefs;

    tableParams['rowCallback'] = createRowCallback(linkFormatString);

    if (!window.tableWidgets)
        window.tableWidgets = {};

    window.tableWidgets[`#${tableId}`] = new TableWidget(
        tableId,
        table.DataTable(tableParams)
    );

    if (refresh)
        setRefresh(tableId, refreshInterval);
}

function setRefresh(tableId, interval) {
    setInterval(function () {
        window.tableWidgets[`#${tableId}`].table.ajax.reload();
    }, interval);
}

function createRowCallback(linkFormatString) {
    return function (row, data) {
        $(row).attr('data-record-id', `${data.id}`);

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
    }

    return def;
}


// ------------------------------- special field render methods ------------------------------- //

function renderSelectField(data, type, row, meta) {
    return $('<input>')
        .attr('type', 'checkbox')
        .attr('class', 'form-check-input select-checkbox')
        .attr('data-record-target', row['id'])
        .attr(
            'onclick',
            'selectCheckboxClickHandler(event, $(this))'
        )[0].outerHTML;
}


function renderDeleteField(data, type, row, meta) {
    return $('<a>')
        .attr('href', '#')
        .attr('data-record-target', row['id'])
        .attr('onclick', 'deleteButtonClickHandler(event, $(this))')
        .html('<i class="bi bi-x-lg"></i>')
        [0].outerHTML;
}


function renderSelectHeader(header) {
    const checkbox = $('<input>')
        .attr('type', 'checkbox')
        .attr('class', 'form-check-input select-header-checkbox')
        .attr('data-state', 'off')
        .on('click', function (e) {
            selectHeaderClickHandler(e, $(this));
        });
    header.append(checkbox);
}


function selectHeaderClickHandler(e, checkbox) {
    const table = checkbox.closest('table')
    const tableId = table.attr('id');
    const tableWidget = window.tableWidgets[`#${tableId}`];

    tableWidget.toggleSelectAll(
        checkbox.prop('checked')
    );

    if (table.hasClass('filtered')) {
        tableWidget.updateSelectHeader();
    }
}


// ------------------------------- special field click handlers ------------------------------- //

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
    console.log(input.val());
    console.log(form.find('.submit-btn'));
    form.find('.submit-btn')[0].click();
}
