function tableSetup(
    {
        table_id,
        model_name,
        cols,
        default_order,
        default_order_col,
        paging,
        refresh,
        refresh_interval,
    } = {}
) {
    const tableParams = {};

    tableParams['ajax'] = `/main/models/${model_name}`;
    tableParams['order'] = [[default_order_col, default_order]];
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

    $(`#${table_id}`).DataTable(tableParams);

    if (refresh) {
        setInterval(function () {
            $(`#${table_id}`).DataTable().ajax.reload();
        }, refresh_interval);
    }
}

function createColumnDef (col, index) {
    console.log(col);
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
        [0].outerHTML;
}

function renderDeleteField (data, type, row, meta) {
    return $('<a>')
        .attr('href', '#')
        .attr('data-record-target', row['id'])
        .html('<i class="bi bi-x-lg"></i>')
        [0].outerHTML;
}