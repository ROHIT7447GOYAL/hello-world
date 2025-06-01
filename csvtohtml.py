import os
import pandas as pd
import html

# CSS styling
CSS = """
body {
    font-family: 'Times New Roman', Times, serif;
    background-color: #f9f9f9;
}
table {
    width: 100%;
    border-collapse: collapse;
    background-color: white;
    margin-bottom: 2rem;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
}
th, td {
    padding: 1rem;
    text-align: left;
    border: 1px solid #cccccc;
    font-size: 12px;
}
th {
    background-color: #E1F5FE;
    color: #01579B;
}
tr:nth-child(even) {
    background-color: #F0F4F8;
}
tr:nth-child(odd) {
    background-color: #FFFFFF;
}
tr:hover {
    background-color: #e8f0fe;
}
.table-section {
    margin-bottom: 4rem;
    overflow-x: auto;
}
.dataTables_filter {
    margin-bottom: 20px;
}
.filter-row th {
    padding: 0.5rem;
}
th input, th select {
    width: 100px;
    margin: 0.2rem 0;
}
#global_filter {
    margin-bottom: 20px;
    padding: 5px;
    width: 300px;
}
.select2-container .select2-selection--multiple {
    min-height: 28px;
    border: 1px solid #ccc;
}
.select2-container--default .select2-selection--multiple .select2-selection__choice {
    background-color: #e4e4e4;
    border: 1px solid #aaa;
    border-radius: 4px;
    padding: 2px 5px;
    font-size: 12px;
}
.select2-container--default .select2-selection--multiple .select2-selection__choice__remove {
    color: #999;
    margin-right: 5px;
}
"""

# Script tags for DataTables, jQuery, and Select2 (CDN links)
SCRIPT_TAGS = """
<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.13.4/css/jquery.dataTables.min.css">
<link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.datatables.net/buttons/2.3.6/js/dataTables.buttons.min.js"></script>
<script src="https://cdn.datatables.net/buttons/2.3.6/js/buttons.html5.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
"""

# JavaScript code to initialize DataTables with filters
JS_CODE = """
<script>
$(document).ready(function() {
    console.log('Document ready - Starting DataTables initialization');
    if (typeof jQuery === 'undefined') {
        console.error('jQuery not loaded. Ensure an internet connection for CDN links.');
        return;
    }
    if (typeof $.fn.DataTable === 'undefined') {
        console.error('DataTables not loaded. Ensure an internet connection for CDN links.');
        return;
    }
    if (typeof $.fn.select2 === 'undefined') {
        console.error('Select2 not loaded. Ensure an internet connection for CDN links.');
        return;
    }
    console.log('jQuery, DataTables, and Select2 loaded successfully');

    var tables = [];
    $('.table-section table').each(function(index) {
        var tableId = $(this).attr('id');
        console.log('Initializing table #' + (index + 1) + ': ' + tableId);

        // Add filter row to thead
        var thead = $(this).find('thead');
        var headerRow = thead.find('tr').first();
        var filterRow = $('<tr class="filter-row"></tr>').insertAfter(headerRow);
        headerRow.find('th').each(function() {
            filterRow.append('<th></th>');
        });

        try {
            var table = $(this).DataTable({
                dom: 'Bfrtip',
                buttons: ['csv'],
                searching: true,
                paging: true,
                ordering: true,
                order: [],
                orderCellsTop: true,
                orderMulti: true, // Enable multi-column sorting
                pageLength: 10,
                initComplete: function() {
                    console.log('initComplete for table: ' + tableId);
                    var api = this.api();
                    api.columns().every(function() {
                        var column = this;
                        var header = $(column.header());
                        var colType = header.data('type');
                        var colIndex = column.index();
                        var filterCell = filterRow.find('th').eq(colIndex);

                        console.log('Processing column ' + colIndex + ' in table ' + tableId + ', type: ' + colType);
                        if (colType === 'string') {
                            console.log('Adding Select2 multiple-select dropdown filter for column ' + colIndex);
                            var select = $('<select multiple></select>')
                                .appendTo(filterCell);

                            column.data().unique().sort().each(function(d, j) {
                                if (d !== null && d !== '') {
                                    select.append('<option value="' + d + '">' + d + '</option>');
                                }
                            });

                            select.select2({
                                placeholder: 'Search options...',
                                allowClear: true,
                                width: '100px'
                            });

                            select.on('change', function() {
                                var selectedVals = $(this).val() ? $(this).val().map(val => $.fn.dataTable.util.escapeRegex(val)) : [];
                                console.log('Dropdown filter changed for column ' + colIndex + ': Values="' + selectedVals.join(', ') + '"');
                                try {
                                    var regex = selectedVals.length ? '^(?:' + selectedVals.join('|') + ')$' : '';
                                    column.search(regex, true, false).draw();
                                    console.log('Column filter applied successfully for column ' + colIndex);
                                } catch (e) {
                                    console.error('Error applying column filter for column ' + colIndex, e);
                                }
                            })
                            .on('click', function(e) {
                                e.stopPropagation();
                                console.log('Click on dropdown for column ' + colIndex + ' stopped propagation');
                            });
                        } else if (colType === 'numeric') {
                            console.log('Adding range filter for column ' + colIndex);
                            var minInput = $('<input type="number" placeholder="Min" style="width:80px;" />')
                                .appendTo(filterCell)
                                .on('input', function() {
                                    console.log('Numeric filter (Min) changed for column ' + colIndex + ': ' + $(this).val());
                                    try {
                                        api.draw();
                                        console.log('Numeric filter applied successfully for column ' + colIndex);
                                    } catch (e) {
                                        console.error('Error applying numeric filter for column ' + colIndex, e);
                                    }
                                })
                                .on('click', function(e) {
                                    e.stopPropagation();
                                    console.log('Click on Min input for column ' + colIndex + ' stopped propagation');
                                });

                            var maxInput = $('<input type="number" placeholder="Max" style="width:80px;" />')
                                .appendTo(filterCell)
                                .on('input', function() {
                                    console.log('Numeric filter (Max) changed for column ' + colIndex + ': ' + $(this).val());
                                    try {
                                        api.draw();
                                        console.log('Numeric filter applied successfully for column ' + colIndex);
                                    } catch (e) {
                                        console.error('Error applying numeric filter for column ' + colIndex, e);
                                    }
                                })
                                .on('click', function(e) {
                                    e.stopPropagation();
                                    console.log('Click on Max input for column ' + colIndex + ' stopped propagation');
                                });

                            header.data('minInput', minInput);
                            header.data('maxInput', maxInput);
                        }
                    });

                    // Custom search for numeric range
                    console.log('Setting up custom search function for numeric range filtering');
                    $.fn.dataTable.ext.search.push(
                        function(settings, data, dataIndex) {
                            if (settings.nTable !== api.table().node()) {
                                console.log('Custom search: Skipping table as it does not match current table');
                                return true;
                            }
                            var columns = api.columns().nodes().length;
                            for (var colIndex = 0; colIndex < columns; colIndex++) {
                                var column = api.column(colIndex);
                                var header = $(column.header());
                                if (header.data('type') === 'numeric') {
                                    var minVal = parseFloat(header.data('minInput').val()) || -Infinity;
                                    var maxVal = parseFloat(header.data('maxInput').val()) || Infinity;
                                    var cellValue = parseFloat(data[colIndex]) || 0;
                                    if (cellValue < minVal || cellValue > maxVal) {
                                        console.log('Row filtered out for column ' + colIndex + ': value=' + cellValue + ', min=' + minVal + ', max=' + maxVal);
                                        return false;
                                    }
                                }
                            }
                            return true;
                        }
                    );
                    console.log('Custom search function for numeric range filtering set up successfully');
                }
            });

            // Log sorting events
            console.log('Setting up sorting event listener for table: ' + tableId);
            $(this).find('thead tr:first th').on('click.DT', function() {
                var order = table.order();
                var sortDetails = order.map(function(orderItem) {
                    return 'Column ' + orderItem[0] + ' (' + api.column(orderItem[0]).header().textContent + '): ' + orderItem[1];
                }).join(', ');
                console.log('Sorting triggered: ' + (sortDetails || 'No sorting applied'));
            });

            console.log('DataTables initialized successfully for table: ' + tableId);
            tables.push(table);
        } catch (e) {
            console.error('Error initializing DataTables for table: ' + tableId, e);
        }
    });

    // Global filter across all tables
    console.log('Setting up global filter');
    $('#global_filter').on('input', function() {
        var value = $.fn.dataTable.util.escapeRegex($(this).val());
        console.log('Global filter applied across all tables: "' + value + '"');
        tables.forEach(function(table, index) {
            console.log('Applying global filter to table #' + (index + 1));
            try {
                table.search(value).draw();
                console.log('Global filter applied successfully to table #' + (index + 1));
            } catch (e) {
                console.error('Error applying global filter to table #' + (index + 1), e);
            }
        });
    });

    console.log('DataTables initialization complete');
});
</script>
"""


def main(input_folder):
    # Get list of CSV files
    csv_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.csv')]
    if not csv_files:
        print(f"No CSV files found in {input_folder}")
        return

    # Start HTML with DOCTYPE declaration
    html_content = [
        '<!DOCTYPE html>',
        '<html>',
        '<head>',
        '<title>CSV Tables</title>',
        '<style>',
        CSS,
        '</style>',
        SCRIPT_TAGS,
        '</head>',
        '<body>',
        '<h1>CSV Tables</h1>',
        '<input type="text" id="global_filter" placeholder="Search all tables...">',
        '<p style="font-size: 12px; color: #555;">Hold Shift and click column headers to sort by multiple columns.</p>'
    ]

    for csv_file in csv_files:
        filename = os.path.splitext(csv_file)[0]
        try:
            df = pd.read_csv(os.path.join(input_folder, csv_file))
            # Trim whitespace from string columns (optional, uncomment if needed)
            # df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        except Exception as e:
            print(f"Error reading {csv_file}: {e}")
            continue
        table_id = 'table_' + filename.replace(' ', '_').replace('.', '_')
        html_table = df.to_html(index=False, table_id=table_id)

        # Add data-type attributes to th elements
        for col, dtype in zip(df.columns, df.dtypes):
            escaped_col = html.escape(str(col))
            col_type = 'numeric' if pd.api.types.is_numeric_dtype(dtype) else 'string'
            html_table = html_table.replace(f'<th>{escaped_col}</th>', f'<th data-type="{col_type}">{escaped_col}</th>')

        html_content.append(f'<div class="table-section"><h2>{filename}</h2>{html_table}</div>')

    html_content.append(JS_CODE)
    html_content.append('</body>')
    html_content.append('</html>')

    # Write to file
    output_path = r'C:\Users\rohit\Documents\csvtohtml\output1.html'
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_content))
        print(f"Output written to {output_path}")
    except Exception as e:
        print(f"Error writing to {output_path}: {e}")


if __name__ == '__main__':
    input_folder = r'C:\Users\rohit\Documents\csvtohtml'
    main(input_folder)