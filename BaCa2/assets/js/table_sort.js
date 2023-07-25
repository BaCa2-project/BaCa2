/**
 * Sorts an HTML table by a column. Supports sorting for tables with a single <tbody> element.
 *
 * @param {HTMLTableElement} table table to sort
 * @param {number} column index of column to sort by
 * @param {boolean} asc determines if the sorting will be in ascending order
 */
function sortTableByColumn(table, column, asc = true) {
    const dirModifier = asc ? 1 : -1;
    const tableBody = table.tBodies[0];
    const rows = Array.from(tableBody.querySelectorAll("tr"));

    const sortedRows = rows.sort((row1, row2) => {
        const aColText = row1.querySelector(`td:nth-child(${ column + 1 })`).textContent.trim();
        const bColText = row2.querySelector(`td:nth-child(${ column + 1 })`).textContent.trim();

        return aColText > bColText ? (1 * dirModifier) : (-1 * dirModifier);
    })

    while (tableBody.firstChild) {
        tableBody.removeChild(tableBody.firstChild);
    }

    tableBody.append(...sortedRows);

    table.querySelectorAll('th').forEach(th =>
        th.classList.remove('th-sort-asc', "th-sort-desc"));
    table.querySelector(`th:nth-child(${ column + 1})`).classList.toggle('th-sort-asc', asc);
    table.querySelector(`th:nth-child(${ column + 1})`).classList.toggle('th-sort-desc', !asc);

    tableBody.querySelectorAll('tr').forEach(tr => {
        tr.querySelectorAll('td').forEach(td => td.classList.remove('td-sort'));
        tr.querySelector(`td:nth-child(${ column + 1})`).classList.toggle('td-sort', true);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.table-sortable th').forEach(headerCell => {
        headerCell.classList.toggle('clickable', true);
        headerCell.addEventListener('click', (ev) => {
            const tableElement = headerCell.parentElement.parentElement.parentElement;
            const headerIndex = Array.prototype.indexOf.call(headerCell.parentElement.children, headerCell);
            const currentIsAscending = headerCell.classList.contains("th-sort-asc");

            sortTableByColumn(tableElement, headerIndex, !currentIsAscending);
        });
    });
});