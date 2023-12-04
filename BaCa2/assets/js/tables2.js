function tableSetup(
    {
        table_id,
        model_name,
        cols,
        default_order,
        default_order_col,
        paging
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
}

function createColumnDef (col, index) {
    const def = {
        'targets': [index],
        'orderable': JSON.parse(col['sortable']),
    };

    if (JSON.parse(col['auto_width'])) {
        def['autoWidth'] = true;
        def['width'] = null;
    }

    if (col['name'] === 'select')
        def['render'] = renderSelectField
    if (col['name'] === 'delete')
        def['render'] = renderDeleteField

    return def;
}

function renderSelectField (data, type, row, meta) {
    return $('<input>')
        .attr('type', 'checkbox')
        .attr('class', 'form-check-input select-checkbox')
        .attr('data-record-target', row['id'])
        [0].outerHTML
}

function renderDeleteField (data, type, row, meta) {
    return $('<input>')
        .attr('type', 'checkbox')
        .attr('class', 'form-check-input select-checkbox')
        .attr('data-record-target', row['id'])
        [0].outerHTML
}