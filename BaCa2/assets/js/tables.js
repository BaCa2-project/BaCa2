function create_table(
    {
        tables_dict,
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
    table_params['ajax'] = `/main/models/${model_name}`;
    table_params['order'] = [[default_order_col, default_order]];

    const cols_data = [];
    for (let i = 0; i < cols.length; i++) {
            cols_data.push({'data': cols[i]});
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
    } else {
        table_params['paging'] = false;
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
            'targets': [record_methods['select']['col_index']],
            'data': null,
            'render': function (data, type, row, meta) {
                return render_checkbox(`checkbox-${row.id}`, table_id);
            }
        });
    }
    if (record_methods['edit']['on']) {
        column_defs.push({
            'targets': [record_methods['edit']['col_index']],
            'data': null,
            'render': function (data, type, row, meta) {
                return render_method_button('edit');
            }
        });
    }
    if (record_methods['delete']['on']) {
        column_defs.push({
            'targets': [record_methods['delete']['col_index']],
            'data': null,
            'render': function (data, type, row, meta) {
                return render_method_button('delete');
            }
        });
    }
    table_params['columnDefs'] = column_defs;

    table_params['rowCallback'] = function (row, data) {
        $(row).attr('data-record-id', `${data.id}`);
    }

    tables_dict[table_id] = $(`#${table_id}`).dataTable(table_params);

    if (refresh) {
        setInterval(() => {
            tables_dict[table_id].ajax.reload();
        }, refresh_interval);
    }
}

function render_checkbox (id, table_id) {
    const checkbox = document.createElement('div');
    $(checkbox).addClass('select-checkbox');

    const checkbox_child = document.createElement('input');
    $(checkbox_child).addClass('form-check-input');
    $(checkbox_child).prop('type', 'checkbox');
    $(checkbox_child).prop('id', id);
    checkbox_child.setAttribute('onclick', `table_select(this, "${table_id}")`);

    checkbox.appendChild(checkbox_child);
    return checkbox.outerHTML;
}

function render_method_button (method) {
    const button = document.createElement('a');
    $(button).addClass('record-method-link');
    button.innerHTML = $('.table-icons-util').find(`.${method}-icon`)[0].outerHTML
    return button.outerHTML;
}

let shift_pressed = false;
let ctrl_pressed = false;
let last_selected_row = null;
let last_deselected_row = null;

$(document).ready(() => {
    document.addEventListener("keydown", function (e) {
        if (e.key === 'Shift') {
            shift_pressed = true;
        } else if (e.key === 'Control') {
            ctrl_pressed = true;
        }
    })

    document.addEventListener("keyup", function (e) {
        if (e.key === 'Shift') {
            shift_pressed = false;
        } else if (e.key === 'Control') {
            ctrl_pressed = false;
        }
    })
})

function table_select (current_checkbox, table_id) {
    const toggled_row = $(current_checkbox).closest('tr');
    const table = tables[table_id]

    console.log(last_deselected_row);
    console.log(last_selected_row);
    console.log(shift_pressed);
    console.log(ctrl_pressed);

    if ($(current_checkbox).prop('checked')) {
        if (shift_pressed && last_selected_row !== null) {
            toggle_range(
                table,
                [table.row(toggled_row).index(), table.row(last_selected_row).index()]
            )
        }
        last_selected_row = toggled_row;
        last_deselected_row = null;
    } else {
        if (ctrl_pressed && last_deselected_row !== null) {
            toggle_range(
                table,
                [table.row(toggled_row).index(), table.row(last_deselected_row).index()],
                false
            )
        }
        last_selected_row = null;
        last_deselected_row = toggled_row
    }
    update_master_checkbox(table_id)
}

function toggle_range (table, range, on = true) {
    const rows = table.rows({ order: 'applied' }).nodes().to$();
    let selecting = false;
    let last_index = false;

    for (let i = 0; i < rows.length; i++) {
        let row = rows[i];

        if (table.row(row).index() === range[0] || table.row(row).index() === range[1]) {
            if (selecting) {
                last_index = true;
            } else {
                selecting = true;
            }
        }

        if (selecting) {
            let checkbox = $(row).find(".form-check-input");
            if (on && !checkbox.prop('checked')) {
                toggle_checkbox(checkbox);
            } else if (!on && checkbox.prop('checked')) {
                toggle_checkbox(checkbox);
            }
        }

        if (last_index) {
            break;
        }
    }
}

function toggle_all (checkbox, table_id) {
    const table = tables[table_id];
    const rows_indexes = table.rows({ order: 'applied' }).indexes().to$();
    const range = [rows_indexes[0], rows_indexes[rows_indexes.length - 1]];

    if ($(checkbox).data('state') === 'on') {
        $(checkbox).prop({checked: false, indeterminate: false});
        $(checkbox).data('state', 'off');
        toggle_range(table, range, false);
    } else {
        $(checkbox).prop({checked: true, indeterminate: false});
        $(checkbox).data('state', 'on');
        toggle_range(table, range);
    }
}

function update_master_checkbox (table_id) {
    const master_checkbox = $(`#${table_id}`).find('.master-checkbox');
    const table = tables[table_id];
    const rows = table.rows().nodes().to$();
    let all_selected = true;
    let all_deselected = true;

    for (let i = 0; i < rows.length; i++) {
        let row = rows[i];
        let checkbox = $(row).find(".form-check-input");

        if (checkbox.prop('checked')) {
            all_deselected = false;
        } else {
            all_selected = false;
        }

        if (!all_deselected && !all_selected) {
            master_checkbox.prop({checked: false, indeterminate: true});
            master_checkbox.data('state', 'indeterminate');
            return;
        }
    }

    if (all_selected) {
        master_checkbox.prop({checked: true, indeterminate: false});
        master_checkbox.data('state', 'on');
    } else {
        master_checkbox.prop({checked: false, indeterminate: false});
        master_checkbox.data('state', 'off');
    }
}

function toggle_checkbox (checkbox) {
    if (checkbox.prop('checked')) {
        checkbox.prop('checked', false);
    } else {
        checkbox.prop('checked', true);
    }
}