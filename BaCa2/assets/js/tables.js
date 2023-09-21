function create_table(
    {
        tables,
        table_id,
        model_name,
        access_mode,
        cols,
        default_order,
        default_order_col,
        paging,
        page_length,
        length_change,
        length_menu,
        non_sortable_indexes,
        record_methods,
        refresh,
        refresh_interval,
    } = {}
) {
    const table_params = {};
    table_params['ajax'] = `main/json/${model_name}-${access_mode}`;

    const cols_data = [];
    for (let col_name in cols) {
        cols_data.push({'data': col_name});
    }
    table_params['columns'] = cols_data;

    if (paging) {
        table_params['pageLength'] = page_length;

        if (length_change) {
            const length_menu_vals = [];
            const length_menu_labels = [];

            for (let length in length_menu) {
                length_menu_vals.push(length);

                if (length !== -1) {
                    length_menu_labels.push(`${length}`);
                } else {
                    length_menu_labels.push('All');
                }
            }

            table_params['lengthMenu'] = [length_menu_vals, length_menu_labels];
        } else {
            table_params['lengthChange'] = false;
        }
    }

    table_params['searching'] = false;

    const column_defs = [];
    if (non_sortable_indexes.length > 0) {
        column_defs.push({
            'targets': non_sortable_indexes,
            'orderable': false
        });
    }
    if (record_methods['select']['on']) {
        column_defs.push({
            'targets': record_methods['select']['col_index'],
            'data': null,
            'render': function (data, type, row, meta) {
                return render_checkbox(`checkbox-${row.id}`);
            }
        });
    }
    if (record_methods['edit']['on']) {
        column_defs.push({
            'targets': record_methods['edit']['col_index'],
            'data': null,
            'render': function (data, type, row, meta) {
                return render_checkbox(`checkbox-${row.id}`);
            }
        });
    }
    table_params['columnDefs'] = column_defs;

    tables[table_id] = $(`#${table_id}`).DataTable({
        ajax: `main/json/${model_name}-${access_mode}`,
        columns: cols_data,
        order: [[default_order_col, default_order]],

    });
}

function render_checkbox (id) {
    const checkbox = document.createElement('div');
    $(checkbox).addClass('select-checkbox');

    const checkbox_child = document.createElement('input');
    $(checkbox_child).addClass('form-check-input');
    $(checkbox_child).prop('type', 'checkbox');
    $(checkbox_child).prop('id', id);
    checkbox_child.setAttribute('onclick', 'table_select(this)');

    checkbox.appendChild(checkbox_child);
    return checkbox.outerHTML;
}

function render_method_button (method) {
    const button = document.createElement('a');
    $(button).addClass('record-method-link');
    const icon = $('.table-icons-util').find(`.${method}-icon`);
    button.appendChild(icon[0]);
    return button.outerHTML;
}


let shift_pressed = false;
let last_selected_row = null;

document.addEventListener("keydown", function (e) {
    if (e.key === 'Shift') {
        shift_pressed = true;
    }
})

document.addEventListener("keyup", function (e) {
    if (e.key === 'Shift') {
        shift_pressed = false;
    }
})

function table_select (current_checkbox) {
    if ($(current_checkbox).prop('checked')) {
        const selected_row = $(current_checkbox).closest('tr');

        if (shift_pressed === true && last_selected_row !== null) {
            const selected_row_index = table.row(selected_row).index();
            const last_selected_row_index = table.row(last_selected_row).index();
            const rows = table.rows({ order: 'applied' }).nodes().to$();
            let selecting = false;

            for (let i = 0; i < rows.length; i++) {
                let row = rows[i];

                if (selecting) {
                    if (table.row(row).index() === selected_row_index ||
                    table.row(row).index() === last_selected_row_index) {
                        break;
                    } else {
                        let checkbox = $(row).find(".form-check-input");
                        if (!checkbox.prop('checked')) {
                            checkbox.prop('checked', true);
                        }
                    }
                } else {
                    if (table.row(row).index() === selected_row_index ||
                    table.row(row).index() === last_selected_row_index) {
                        selecting = true;
                    }
                }
            }
        }

        last_selected_row = selected_row;
    } else {
        last_selected_row = null;
    }
}