document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.search-input').forEach(inputField => {
        const tableRows = inputField.closest('table').querySelectorAll('tbody tr');
        const headerCell = inputField.closest('th');
        const header = inputField.closest('tr').querySelectorAll('th');
        const columnIndex = Array.from(header).indexOf(headerCell);
        const searchableCells = Array.from(tableRows).map(
            row => row.querySelectorAll('td')[columnIndex]);

        inputField.addEventListener('input', (ev) => {
            const table = inputField.closest('table');
            table.querySelectorAll('.search-input').forEach(field => {
                if (field !== inputField) {
                    field.value = '';
                }
            });

            const searchQuery = inputField.value.toLowerCase();

            for (const cell of searchableCells) {
                const row = cell.closest('tr');
                const value = cell.textContent.toLowerCase().replace(',', '');

                row.style.visibility = null;

                if (value.search(searchQuery) === -1) {
                    row.style.visibility = 'collapse';
                    row.classList.remove('search-match');
                }
                else {
                    row.classList.toggle('search-match', true)
                }
            }
        });
        inputField.addEventListener('click', (ev) => {
            ev.stopPropagation();
        });
    });
});