class TableWidget {
    constructor(tableId, table) {
        this.tableId = tableId;
        this.table = table;
        this.lastSelectedRow = null;
        this.lastDeselectedRow = null;
    }

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
        this.getRowsInOrder().each(function () {
            $(this).find('.select-checkbox').prop('checked', on);

            if (on)
                $(this).addClass('row-selected');
            else
                $(this).removeClass('row-selected');
        });
    }

    updateSelectHeader() {
        const headerCheckbox = $(`#${this.tableId} .select-header-checkbox`);
        let allSelected = true;
        let noneSelected = true;

        this.getRowsInOrder().each(function () {
            if ($(this).hasClass('row-selected'))
                noneSelected = false;
            else
                allSelected = false;
        });

        if (allSelected) {
            headerCheckbox.prop('checked', true);
            headerCheckbox.prop('indeterminate', false);
            headerCheckbox.data('state', 'on');
        } else if (noneSelected) {
            headerCheckbox.prop('checked', false);
            headerCheckbox.prop('indeterminate', false);
            headerCheckbox.data('state', 'off');
        } else {
            headerCheckbox.prop('checked', false);
            headerCheckbox.prop('indeterminate', true);
            headerCheckbox.data('state', 'indeterminate');
        }
    }

    getRowsInOrder() {
        return this.table.rows({ order: 'applied' }).nodes().to$();
    }

    getRowIndex(row) {
        return this.table.row(row).index();
    }

    hasLastSelectedRow() {
        return this.lastSelectedRow !== null;
    }

    hasLastDeselectedRow() {
        return this.lastDeselectedRow !== null;
    }
}


function initTable(
    {
        tableId,
        modelName,
        cols,
        defaultOrder,
        defaultOrderCol,
        paging,
        refresh,
        refreshInterval,
    } = {}
) {
    const tableParams = {};

    tableParams['ajax'] = `/main/models/${modelName}`;
    tableParams['order'] = [[defaultOrderCol, defaultOrder]];
    tableParams['searching'] = false;

    const columns = [];
    cols.forEach(col => {columns.push({'data': col['name']})});
    tableParams['columns'] = columns;

    if (paging) {
        tableParams['pageLength'] = paging['page_length'];

        if (paging['allow_length_change']) {
            const pagingMenuVals = [];
            const pagingMenuLabels = [];

            paging['length_change_options'].forEach(option => {
                pagingMenuVals.push(option);
                pagingMenuLabels.push(option === -1 ? 'All' : `${option}`);
            })

            tableParams['lengthMenu'] = [pagingMenuVals, pagingMenuLabels];
        }
    } else
        tableParams['paging'] = false;

    const columnDefs = [];
    cols.forEach(col => columnDefs.push(createColumnDef(col, cols.indexOf(col))));
    tableParams['columnDefs'] = columnDefs;

    tableParams['rowCallback'] = function (row, data) {
        $(row).attr('data-record-id', `${data.id}`);
    }

    if (!window.tableWidgets)
        window.tableWidgets = {};

    window.tableWidgets[`#${tableId}`] = new TableWidget(
        tableId,
        $(`#${tableId}`).DataTable(tableParams)
    )

    if (refresh) {
        setInterval(function () {
            window.tableWidgets[`#${tableId}`].table.ajax.reload();
        }, refreshInterval);
    }
}


function createColumnDef (col, index) {
    const def = {
        'targets': [index],
        'orderable': JSON.parse(col['sortable']),
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
    }

    return def;
}


function renderSelectField (data, type, row, meta) {
    return $('<input>')
        .attr('type', 'checkbox')
        .attr('class', 'form-check-input select-checkbox')
        .attr('data-record-target', row['id'])
        .attr(
            'onclick',
            'selectCheckboxClickHandler(event, $(this))'
        )[0].outerHTML;
}


function renderDeleteField (data, type, row, meta) {
    return $('<a>')
        .attr('href', '#')
        .attr('data-record-target', row['id'])
        .html('<i class="bi bi-x-lg"></i>')
        [0].outerHTML;
}


function renderSelectHeader (header) {
    const checkbox = $('<input>')
        .attr('type', 'checkbox')
        .attr('class', 'form-check-input select-header-checkbox')
        .attr('data-state', 'off')
        .on('click', function (e) {
            selectHeaderClickHandler(e, $(this));
        });
    header.append(checkbox);
}


function selectHeaderClickHandler (e, checkbox) {
    window.tableWidgets[`#${checkbox.closest('table').attr('id')}`].toggleSelectAll(
        checkbox.prop('checked')
    );
}


function selectCheckboxClickHandler (e, checkbox) {
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

function tablesSetup() {
    $('th.select').each(function () {
        renderSelectHeader($(this));
    });
}