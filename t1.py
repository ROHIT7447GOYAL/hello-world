import re
import pandas as pd
import numpy as np
from datetime import datetime
import os
import difflib
import glob
import datetime





# Define the directory path
directory = os.path.join("C:\\", "Users", "rohit", "Documents", "stocks")

# Pattern to match positions.csv or positions(number).csv
pattern = os.path.join(directory, "positions*.csv")

# Get all files matching the pattern
matching_files = glob.glob(pattern)

# Filter files to ensure they match positions.csv or positions(number).csv
valid_files = [
    f for f in matching_files
    if re.match(r'.*positions(\(\d+\))?\.csv$', f)
]

# Find the most recently created file and delete others
if valid_files:
    input_path = max(valid_files, key=os.path.getctime)
    print(f"Keeping latest file: {input_path}")

    # Delete all other matching files
    for file in valid_files:
        if file != input_path:
            try:
                os.remove(file)
                print(f"Deleted file: {file}")
            except OSError as e:
                print(f"Error deleting file {file}: {e}")
else:
    raise FileNotFoundError("No files matching 'positions*.csv' found in the directory.")


INPUT_CSV = input_path
OUTPUT_HTML = 'output.html'

def extract_stock(instr):
    """Extract stock code from instrument name."""
    m = re.match(r'^([A-Za-z]+)', instr)
    return m.group(1) if m else instr

def main():
    """Process positions.csv, generate financial metrics, and output to HTML."""
    # Set watchlist file path dynamically using os.path.join
    current_date = datetime.date.today()
    month = current_date.strftime("%B")
    day = current_date.day
    year = current_date.year
    # Set base path and output path
    base_path = r"C:\Users\rohit\Documents\stocks"


    # Set today's date dynamically
    today = datetime.date.today()
    date_str = f"{today.strftime('%B')} {today.day}, {today.year}"

    # Define the directory path
    folder_path = base_path

    # Patterns to match Collar_{date_str}*.csv and ALL PARAMETERS_{date_str}*.csv
    collar_pattern = os.path.join(folder_path, f"Collar_{date_str}*.csv")
    params_pattern = os.path.join(folder_path, f"ALL PARAMETERS_{date_str}*.csv")

    # Get all files matching the patterns
    collar_files = glob.glob(collar_pattern)
    params_files = glob.glob(params_pattern)

    # Filter files to match Collar_{date_str}*.csv or Collar_{date_str}(number).csv
    valid_collar_files = [
        f for f in collar_files
        if re.match(rf'.*Collar_{re.escape(date_str)}(\(\d+\))?\.csv$', f)
    ]

    print(collar_pattern)
    print(valid_collar_files)


    # Filter files to match ALL PARAMETERS_{date_str}*.csv or ALL PARAMETERS_{date_str}(number).csv
    valid_params_files = [
        f for f in params_files
        if re.match(rf'.*ALL PARAMETERS_{re.escape(date_str)}(\(\d+\))?\.csv$', f)
    ]

    # Process Collar files: Keep the latest, delete others
    if valid_collar_files:
        today_collar = max(valid_collar_files, key=os.path.getctime)
        print(f"Keeping latest Collar file: {today_collar}")
        for file in valid_collar_files:
            if file != today_collar:
                try:
                    os.remove(file)
                    print(f"Deleted {file}")
                except OSError as e:
                    print(f"Error deleting file {file}: {e}")
    else:
        print(f"No files matching 'Collar_{date_str}*.csv' found in the directory.")

    # Process ALL PARAMETERS files: Keep the latest, delete others
    if valid_params_files:
        today_params = max(valid_params_files, key=os.path.getctime)
        print(f"Keeping latest ALL PARAMETERS file: {today_params}")
        for file in valid_params_files:
            if file != today_params:
                try:
                    os.remove(file)
                    print(f"Deleted {file}")
                except OSError as e:
                    print(f"Error deleting file {file}: {e}")
    else:
        print(f"No files matching 'ALL PARAMETERS_{date_str}*.csv' found in the directory.")



    watchlist_path =today_collar

    # Read positions data
    try:
        df = pd.read_csv(INPUT_CSV)
        print(df)
        df.columns = df.columns.str.strip()
    except FileNotFoundError:
        print(f"Error: {INPUT_CSV} not found.")
        return
    df['stock'] = df['Instrument'].astype(str).apply(extract_stock)

    # Read watchlist data
    try:
        watchlist_df = pd.read_csv(watchlist_path)
        watchlist_df.columns = watchlist_df.columns.str.strip()
        print("Watchlist columns:", watchlist_df.columns)
        watchlist_stocks = watchlist_df['NSE Code'].str.upper().str.strip().unique()
        # Identify high-value stocks
        if all(col in watchlist_df.columns for col in ['TL Valuation Score', 'TL Momentum Score', 'TL Durability Score']):
            high_value_stocks = watchlist_df[
                (watchlist_df['TL Valuation Score'] > 40) &
                (watchlist_df['TL Momentum Score'] > 50) &
                (watchlist_df['TL Durability Score'] > 50)
            ]['NSE Code'].str.upper().str.strip().unique()
        else:
            high_value_stocks = []
    except FileNotFoundError:
        print(f"Error: {watchlist_path} not found. Please ensure the file exists at the specified path.")
        watchlist_df = pd.DataFrame(columns=['NSE Code', 'LTP', 'Change (%)', 'TL Durability Score', 'TL Valuation Score', 'TL Momentum Score', 'Stock Classification'])
        watchlist_stocks = []
        high_value_stocks = []
    except KeyError as e:
        print(f"Error: Column {e} not found in watchlist. Available columns:", watchlist_df.columns if 'watchlist_df' in locals() else "None")
        watchlist_df = pd.DataFrame(columns=['NSE Code', 'LTP', 'Change (%)', 'TL Durability Score', 'TL Valuation Score', 'TL Momentum Score', 'Stock Classification'])
        watchlist_stocks = []
        high_value_stocks = []

    # ==== MAIN REPORT ====
    records = []
    for stock, grp in df.groupby('stock'):
        futs = grp[grp['Instrument'].str.contains('FUT')]
        if futs.empty:
            continue
        fut = futs.iloc[0]
        pe_rows = grp[grp['Instrument'].str.contains('PE')]
        ce_rows = grp[grp['Instrument'].str.contains('CE')]

        if fut['Qty.'] != 0:
            margin_total = fut['Qty.'] * fut['Avg.']
            margin_pct = fut['Chg.']
            margin_pl = fut['P&L']
            pe_pl = pe_rows['P&L'].sum() if not pe_rows.empty else 0
            ce_pl = ce_rows['P&L'].sum() if not ce_rows.empty else 0
            total_prem = pe_pl + ce_pl
            total_net = margin_pl + total_prem
            net_pct = (total_net / margin_total) * 100 if margin_total else np.nan
            prem_pct = (total_prem / margin_total) * 100 if margin_total else np.nan

            # Collar strategy max loss/profit
            max_loss = np.nan
            max_profit = np.nan
            fut_qty = fut['Qty.']
            if not pe_rows.empty:
                pe_strikes = [float(m.group(1)) for inst in pe_rows['Instrument'] if (m := re.search(r'(\d+(?:\.\d+)?)PE', inst))]
                if pe_strikes:
                    K_pe = np.mean(pe_strikes)
                    pe_avg = pe_rows['Avg.'].mean()
                    pe_qty = pe_rows['Qty.'].sum()
                    if pe_qty == fut_qty:
                        max_loss = fut_qty * (K_pe - fut['Avg.'] - pe_avg + (ce_rows['Avg.'].mean() if not ce_rows.empty else 0))
            if not ce_rows.empty:
                ce_strikes = [float(m.group(1)) for inst in ce_rows['Instrument'] if (m := re.search(r'(\d+(?:\.\d+)?)CE', inst))]
                if ce_strikes:
                    K_ce = np.mean(ce_strikes)
                    ce_avg = ce_rows['Avg.'].mean()
                    ce_qty = ce_rows['Qty.'].sum()
                    if ce_qty == -fut_qty:
                        max_profit = fut_qty * (K_ce - fut['Avg.'] - (pe_rows['Avg.'].mean() if not pe_rows.empty else 0) + ce_avg)

            records.append({
                'stockcode': stock,
                'margin_total': margin_total,
                'margin_%': margin_pct,
                'margin_p/l': margin_pl,
                'total_premium': total_prem,
                'total_premium_%': prem_pct,
                'total_net': total_net,
                'net_%': net_pct,
                'max_loss': max_loss,
                'max_profit': max_profit
            })

    df_main = pd.DataFrame(records).sort_values('total_net', ascending=False)

    tot_margin = df_main['margin_total'].sum()
    tot_pl = df_main['margin_p/l'].sum()
    tot_prem = df_main['total_premium'].sum()
    tot_net = df_main['total_net'].sum()
    footer = {
        'stockcode': 'TOTAL',
        'margin_total': tot_margin,
        'margin_%': (tot_pl / tot_margin) * 100 if tot_margin else np.nan,
        'margin_p/l': tot_pl,
        'total_premium': tot_prem,
        'total_premium_%': (tot_prem / tot_margin) * 100 if tot_margin else np.nan,
        'total_net': tot_net,
        'net_%': (tot_net / tot_margin) * 100 if tot_margin else np.nan,
        'max_loss': np.nan,
        'max_profit': np.nan
    }

    # ==== CE FILTER BLOCK ====
    ce_all = df[df['Instrument'].str.contains('CE')].copy()
    ce_all['stock'] = ce_all['Instrument'].apply(extract_stock)
    ce_grouped = ce_all.groupby('stock').filter(lambda g: (g['Chg.'] != 0.000007).any())

    pe_all = df[df['Instrument'].str.contains('PE')].copy()
    pe_all['stock'] = pe_all['Instrument'].apply(extract_stock)
    pe_grouped = pe_all.groupby('stock').filter(lambda g: (g['Chg.'] != 0.000007).any())

    ce_merge = ce_grouped[['stock', 'Avg.', 'LTP', 'Chg.']].rename(columns={'Avg.': 'Avg_ce', 'LTP': 'LTP_ce', 'Chg.': 'Chg%'})
    pe_avg = pe_grouped.groupby('stock')['Avg.'].mean().reset_index().rename(columns={'Avg.': 'PE_AVG'})

    ce_merge = ce_merge.merge(pe_avg, on='stock', how='left')
    ce_merge['CE diff'] = ce_merge['Avg_ce'] - ce_merge['LTP_ce']
    ce_merge['diff int'] = ce_merge['Avg_ce'] - ce_merge['PE_AVG']

    df_ce = ce_merge[(ce_merge['CE diff'] > ce_merge['PE_AVG']) & (ce_merge['CE diff'] > ce_merge['diff int'])]
    df_ce = df_ce[['stock', 'Avg_ce', 'LTP_ce', 'Chg%', 'PE_AVG', 'CE diff', 'diff int']]
    df_ce.columns = ['stockcode', 'Avg_ce', 'LTP_ce', 'Chg%', 'PE AVG', 'CE diff', 'diff int']
    highlights = set(df_ce['stockcode'].str.upper().str.strip())

    # ==== MOVEMENT BLOCK ====
    move_records = []
    for stock, grp in df.groupby('stock'):
        fut = grp[grp['Instrument'].str.contains('FUT')]
        if fut.empty:
            continue
        fut = fut.iloc[0]
        stock_avg = fut['Avg.']
        stock_ltp = fut['LTP']
        stock_chg = fut['Chg.']
        pe_list = grp[grp['Instrument'].str.contains('PE')]
        pe_points = [float(m.group(1)) for inst in pe_list['Instrument'] if (m := re.search(r'(\d+(?:\.\d+)?)PE', inst))]
        pe_point = np.mean(pe_points) if pe_points else 0
        ce_list = grp[grp['Instrument'].str.contains('CE')]
        ce_points = [float(m.group(1)) for inst in ce_list['Instrument'] if (m := re.search(r'(\d+(?:\.\d+)?)CE', inst))]
        ce_point = np.mean(ce_points) if ce_points else 0
        move_ce = (ce_point - stock_avg) / stock_avg * 100 if ce_point and stock_avg != 0 else 0
        move_pe = (stock_avg - pe_point) / stock_avg * 100 if pe_point and stock_avg != 0 else 0
        left_ce = (ce_point - stock_ltp) / stock_ltp * 100 if ce_point and stock_ltp != 0 else 0
        left_pe = (stock_ltp - pe_point) / stock_ltp * 100 if pe_point and stock_ltp != 0 else 0

        if not ce_all[ce_all['stock'] == stock].empty:
            avg_ce = ce_all[ce_all['stock'] == stock]['Avg.'].mean()
            ltp_ce = ce_all[ce_all['stock'] == stock]['LTP'].mean()
        else:
            avg_ce = 0
            ltp_ce = 0
        if not pe_all[pe_all['stock'] == stock].empty:
            avg_pe = pe_all[pe_all['stock'] == stock]['Avg.'].mean()
            ltp_pe = pe_all[pe_all['stock'] == stock]['LTP'].mean()
        else:
            avg_pe = 0
            ltp_pe = 0
        diff_int = avg_ce - avg_pe
        ltp_ce1=0
        ltp_pe1=0
        if avg_ce > 0:
            ltp_ce1=avg_ce - ltp_ce

        if avg_pe > 0:
            ltp_pe1 = ltp_pe - avg_pe

        ltp_diff = ltp_ce1 + ltp_pe1



        premium_pct = diff_int / stock_avg * 100 if stock_avg else 0
        current_pct = ltp_diff / stock_avg * 100 if stock_avg else 0
        left_ce_prem = left_ce + premium_pct if ce_point != 0 else 100
        left_pe_prem = left_pe + premium_pct

        diff =current_pct-premium_pct

        if fut['Qty.'] != 0:
            move_records.append({
                'stockcode': stock,
                'ce_point': ce_point,
                'pe_point': pe_point,
                'stock_chg_%': stock_chg,
                'stock_avg': stock_avg,

                'stock_ltp': stock_ltp,
                'left ce (%)': left_ce,
                'left pe (%)': left_pe,
                'ltp ce' :ltp_ce,
                'ltp pe' :ltp_pe,
                'avg ce': avg_ce,
                'avg_pe': avg_pe,
                'current % ': current_pct,
                'premium %': premium_pct,
                'diff %': diff,
                'left ce prem (%)': left_ce_prem,
                'left pe prem (%)': left_pe_prem,
                'move ce (%)': move_ce,
                'move pe (%)': move_pe
            })

    df_move = pd.DataFrame(move_records)

    # Debug stock lists
    main_stocks = df_main['stockcode'].str.upper().str.strip().unique()
    not_in_main = [stock for stock in watchlist_stocks if stock not in main_stocks]
    not_in_watchlist = [stock for stock in main_stocks if stock not in watchlist_stocks]
    print("Main stocks:", main_stocks)
    print("Watchlist stocks:", watchlist_stocks)
    print("Not in main:", not_in_main)

    # ==== WATCHLIST STOCKS NOT IN POSITIONS ====
    try:
        columns_to_select = ['NSE Code', 'LTP', 'Change (%)', 'TL Durability Score', 'TL Valuation Score', 'TL Momentum Score', 'Stock Classification']
        available_columns = [col for col in columns_to_select if col in watchlist_df.columns]
        not_in_main_df = watchlist_df[watchlist_df['NSE Code'].str.upper().str.strip().isin(not_in_main)][available_columns].copy()
        not_in_main_df.rename(columns={'NSE Code': 'stockcode', 'LTP': 'current_price', 'Change (%)': 'change_%'}, inplace=True)
    except KeyError as e:
        print(f"Error: Column not found in watchlist. {e}. Available columns:", watchlist_df.columns)
        not_in_main_df = pd.DataFrame(columns=['stockcode', 'current_price', 'change_%', 'TL Durability Score', 'TL Valuation Score', 'TL Momentum Score', 'Stock Classification'])

    # ==== POSITIONS NOT IN WATCHLIST ====
    not_in_watchlist_df = df_main[df_main['stockcode'].str.upper().str.strip().isin(not_in_watchlist)]

    # Read stock_codes.csv and compute matched_stockcodes
    try:
        stock_codes_df = pd.read_csv(r"C:\Users\rohit\Documents\stocks\stock_codes.csv")
        m_stock_codes = stock_codes_df['m_stock_code'].str.upper().str.strip().unique().tolist()
    except FileNotFoundError:
        print("Error: stock_codes.csv not found.")
        m_stock_codes = []
    except KeyError:
        print("Error: 'm_stock_code' column not found in stock_codes.csv.")
        m_stock_codes = []

    all_stockcodes = set()
    for df in [df_main, df_ce, df_move]:
        if 'stockcode' in df.columns:
            all_stockcodes.update(df['stockcode'].str.upper().str.strip())
    if 'stockcode' in not_in_main_df.columns:
        all_stockcodes.update(not_in_main_df['stockcode'].str.upper().str.strip())
    if 'stockcode' in not_in_watchlist_df.columns:
        all_stockcodes.update(not_in_watchlist_df['stockcode'].str.upper().str.strip())

    matched_stockcodes = set()
    for stockcode in all_stockcodes:
        matches = difflib.get_close_matches(stockcode, m_stock_codes, n=1, cutoff=0.9)
        if matches:
            matched_stockcodes.add(stockcode)
    print("active broker report")
    print(matched_stockcodes)

    # ==== HTML OUTPUT ====
    html = []
    html.append("""
    <html>
    <head>
        <title>Financial Report</title>
        <style>
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
                font-size: 1.1rem;
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
            .total td {
                font-weight: bold;
            }
            .highlight { background-color: yellow; }
            .warn { background-color: orange; }
            .highlight_cell_main { background-color: lightyellow; }
            .highlight_cell_move { background-color: lightcyan; }
            .high_value { background-color: lightgreen; }
            .not_in_watchlist { background-color: #FFECB3; }
            .net_highlight { background-color: lightgreen; }
            .collar_credit { background-color: #C8E6C9; } /* Light green for net credit */
            .recent_match { background-color: #E6F0FA; } /* Rose for matched stocks */
            .table-controls {
                display: flex;
                align-items: center;
                gap: 1rem;
                margin-bottom: 1rem;
            }
            .filter-btn, .color-filter, .dt-buttons button {
                margin: 0;
                padding: 0.5rem 1rem;
                cursor: pointer;
                background-color: #E1F5FE;
                color: #01579B;
                border: none;
            }
            .filter-btn:hover, .color-filter:hover, .dt-buttons button:hover {
                background-color: #B3E5FC;
            }
            .color-filter {
                border: 1px solid #4DD0E1;
            }
            .dataTables_wrapper {
                margin-bottom: 2rem;
            }
            .dataTables_filter {
                margin-bottom: 2rem;
                float: right;
            }
            .dataTables_filter label, .dataTables_length label {
                font-weight: bold;
            }
            .dataTables_info {
                font-style: italic;
            }
            .dt-buttons {
                margin: 0;
            }
            
            .table-section {
                margin-bottom: 4rem;
                overflow-x: auto;
            }
            .filter-row th {
                padding: 0.5rem;
            }
            th input, th select {
                width: 100px;
                margin: 0.2rem 0;
                box-sizing: border-box;
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
            .table-section h2 {
            margin-bottom: 0.1rem; /* Further reduced space between heading and table block */
        }
         th, td {
            padding: 1rem;
            text-align: left;
            border: 1px solid #cccccc;
            font-size: 14px;
        }
        .table-controls {
            display: flex;
            align-items: center;
            gap: 0.3rem;
            margin-bottom: 0.3rem;
            margin-top: 0; /* Ensure no extra space above controls */
        }
        .table-section {
        margin-bottom: 0.5rem;
        overflow-x: auto;
        }
        </style>
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.min.css">
        <link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
        <script src="https://cdn.datatables.net/buttons/2.2.2/js/dataTables.buttons.min.js"></script>
        <script src="https://cdn.datatables.net/buttons/2.2.2/js/buttons.html5.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
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
                $('.table-section').each(function() {
                    var section = $(this);
                    var tableId = section.find('table').attr('id');
                    console.log('Initializing table #' + tableId);

                    // Add filter row to thead
                    var thead = section.find('thead');
                    var headerRow = thead.find('tr').first();
                    var filterRow = $('<tr class="filter-row"></tr>').insertAfter(headerRow);
                    headerRow.find('th').each(function() {
                        filterRow.append('<th></th>');
                    });

                    try {
                        var table = section.find('table').DataTable({
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
                                        var select = $('<select multiple></select>').appendTo(filterCell);

                                        console.log('Populating dropdown options for column ' + colIndex + ': ' + column.data().unique().sort().join(', '));
                                        column.data().unique().sort().each(function(d, j) {
                                            var optionText = String(d).trim();
                                            if (optionText !== '') {
                                                select.append('<option value="' + optionText + '">' + optionText + '</option>');
                                            }
                                        });

                                        select.select2({                                           placeholder: 'Search options...',
                                            allowClear: true,
                                            width: '100px',
                                            minimumInputLength: 0
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

                        // Dynamically determine which highlight classes are present in the table
                             // Dynamically determine which highlight classes are present in the table
                var highlightClasses = new Set();
                table.rows().every(function() {
                    var row = $(this.node());
                    if (row.find('.highlight_cell_main').length > 0) highlightClasses.add('highlight_cell_main');
                    if (row.find('.highlight_cell_move').length > 0) highlightClasses.add('highlight_cell_move');
                    if (row.find('.high_value').length > 0) highlightClasses.add('high_value');
                    if (row.find('.not_in_watchlist').length > 0) highlightClasses.add('not_in_watchlist');
                    if (row.find('.net_highlight').length > 0) highlightClasses.add('net_highlight');
                    if (row.find('.collar_credit').length > 0) highlightClasses.add('collar_credit');
                    if (row.find('.recent_match').length > 0) highlightClasses.add('recent_match');
                });

                // Create color filter dropdown based on present classes with better names
                var dropdownOptions = '<option value="all">Show All Rows</option>';
                if (highlightClasses.has('highlight_cell_main')) dropdownOptions += '<option value="highlight_cell_main">Margin Impact (Yellow)</option>';
                if (highlightClasses.has('highlight_cell_move')) dropdownOptions += '<option value="highlight_cell_move">Movement Alert (Cyan)</option>';
                if (highlightClasses.has('high_value')) dropdownOptions += '<option value="high_value">High Value Stocks (Green)</option>';
                if (highlightClasses.has('not_in_watchlist')) dropdownOptions += '<option value="not_in_watchlist">Not in Watchlist (Amber)</option>';
                if (highlightClasses.has('net_highlight')) dropdownOptions += '<option value="net_highlight">High Net Profit (Green)</option>';
                if (highlightClasses.has('collar_credit')) dropdownOptions += '<option value="collar_credit">Net Credit Collar (Green)</option>';
                if (highlightClasses.has('recent_match')) dropdownOptions += '<option value="recent_match">Matched Stocks (Coral)</option>';

                // Create table-controls div with all buttons and dropdown
                section.prepend('<div class="table-controls"></div>');
                var controls = section.find('.table-controls');
                controls.append('<button class="filter-btn">Show Highlighted Rows Only</button>');
                controls.append('<select class="color-filter">' + dropdownOptions + '</select>');
                // Move the CSV button into table-controls
                section.find('.dt-buttons').detach().appendTo(controls);

                // Add custom filter for DataTables
                $.fn.dataTable.ext.search.push(
                    function(settings, data, dataIndex) {
                        var selectedClass = section.find('.color-filter').val();
                        if (selectedClass === 'all') return true;
                        if (selectedClass === 'highlighted') {
                            var row = table.row(dataIndex).node();
                            return $(row).find('.highlight_cell_main, .highlight_cell_move, .high_value, .not_in_watchlist, .net_highlight, .collar_credit, .recent_match').length > 0;
                        }
                        var row = table.row(dataIndex).node();
                        return $(row).find('.' + selectedClass).length > 0;
                    }
                );

                section.find('.color-filter').change(function() {
                    var selectedClass = $(this).val();
                    console.log("Color filter changed to", selectedClass);
                    table.draw(); // Apply the custom filter
                    table.page(0).draw('page'); // Go to the first page
                });

                section.find('.filter-btn').click(function() {
                    console.log("Filter button clicked, current text:", $(this).text());
                    if ($(this).text() === 'Show Highlighted Rows Only') {
                        section.find('.color-filter').val('highlighted').trigger('change');
                        $(this).text('Show All Rows');
                    } else {
                        section.find('.color-filter').val('all').trigger('change');
                        $(this).text('Show Highlighted Rows Only');
                    }
                });
                        // Log sorting events
                        console.log('Setting up sorting event listener for table: ' + tableId);
                        section.find('thead tr:first th').on('click.DT', function() {
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
    </head>
    <body>
        <h1>Financial Report</h1>
        <input type="text" id="global_filter" placeholder="Search all tables...">
        <p style="font-size: 12px; color: #555;">Hold Shift and click column headers to sort by multiple columns.</p>
        """)

    # Add data-type attributes to tables for filtering
    # Main Table with Cell Highlighting
    html.append('<div class="table-section"><h2>Main Positions</h2><table id="main_positions">')
    html.append('<thead><tr>' + ''.join(f'<th data-type="{"numeric" if c != "stockcode" else "string"}">{c}</th>' for c in df_main.columns) + '</tr></thead>')
    html.append('<tbody>')
    for _, r in df_main.iterrows():
        stockcode = r['stockcode'].upper().strip()
        row_class = 'highlight' if stockcode in highlights else ''
        # Determine if stockcode is matched
        is_matched = stockcode in matched_stockcodes
        # Determine highlighting for stockcode cell
        cell_classes = []
        if stockcode in high_value_stocks:
            cell_classes.append('high_value')
        if stockcode in not_in_watchlist:
            cell_classes.append('not_in_watchlist')
        stockcode_class = ' '.join(cell_classes)
        html.append(f'<tr class="{row_class}">')
        for idx, c in enumerate(df_main.columns):
            if c == 'stockcode':
                cell_class_for_column = stockcode_class
            elif idx == 1 and is_matched:  # Second column (margin_total)
                cell_class_for_column = 'recent_match'
            else:
                cell_class_for_column = 'highlight_cell_main' if c in ['margin_%', 'total_premium_%'] and not np.isnan(
                    r['margin_%']) and not np.isnan(r['total_premium_%']) and abs(r['margin_%']) < 0.6 * r[
                                                                     'total_premium_%'] else ''
                if c == 'net_%' and not np.isnan(r[c]) and r[c] >= 2:
                    cell_class_for_column = 'net_highlight'
                if c == 'initial_net_premium' and not np.isnan(r[c]) and r[c] < 0:
                    cell_class_for_column = 'collar_credit'
            value = f'{r[c]:.2f}' if isinstance(r[c], float) else r[c]
            html.append(f'<td class="{cell_class_for_column}">{value}</td>')
        html.append('</tr>')
    html.append('</tbody>')
    html.append('<tfoot><tr class="total">' + ''.join(
        f'<td>{footer[c]:.2f}</td>' if isinstance(footer[c], float) else f'<td>{footer[c]}</td>' for c in
        df_main.columns) + '</tr></tfoot>')
    html.append('</table></div>')

    # Stocks in Positions but not in Watchlist
    html.append(
        '<div class="table-section"><h2>Stocks in Positions but not in Watchlist</h2><table id="positions_not_watchlist">')
    html.append('<thead><tr>' + ''.join(f'<th data-type="{"numeric" if c != "stockcode" else "string"}">{c}</th>' for c in df_main.columns) + '</tr></thead>')
    html.append('<tbody>')
    for _, r in not_in_watchlist_df.iterrows():
        stockcode = r['stockcode'].upper().strip()
        is_matched = stockcode in matched_stockcodes
        html.append(f'<tr>')
        for idx, c in enumerate(df_main.columns):
            if c == 'stockcode':
                cell_classes = []
                if stockcode in high_value_stocks:
                    cell_classes.append('high_value')
                if stockcode in not_in_watchlist:
                    cell_classes.append('not_in_watchlist')
                cell_class = ' '.join(cell_classes)
            elif idx == 1 and is_matched:  # Second column (margin_total)
                cell_class = 'recent_match'
            else:
                cell_class = ''
                if c == 'initial_net_premium' and not np.isnan(r[c]) and r[c] < 0:
                    cell_class = 'collar_credit'
            value = f'{r[c]:.2f}' if isinstance(r[c], float) else r[c]
            html.append(f'<td class="{cell_class}">{value}</td>')
        html.append('</tr>')
    html.append('</tbody>')
    html.append('</table></div>')

    # CE Filter Table
    html.append('<div class="table-section"><h2>Filtered CE Options</h2><table id="filtered_ce">')
    html.append('<thead><tr>' + ''.join(f'<th data-type="{"numeric" if c != "stockcode" else "string"}">{c}</th>' for c in df_ce.columns) + '</tr></thead>')
    html.append('<tbody>')
    for _, r in df_ce.iterrows():
        stockcode = r['stockcode'].upper().strip()
        is_matched = stockcode in matched_stockcodes
        html.append(f'<tr>')
        for idx, c in enumerate(df_ce.columns):
            if c == 'stockcode':
                cell_classes = []
                if stockcode in high_value_stocks:
                    cell_classes.append('high_value')
                cell_class = ' '.join(cell_classes)
            elif idx == 1 and is_matched:  # Second column (Avg_ce)
                cell_class = 'recent_match'
            else:
                cell_class = ''
            value = f'{r[c]:.2f}' if isinstance(r[c], float) else r[c]
            html.append(f'<td class="{cell_class}">{value}</td>')
        html.append('</tr>')
    html.append('</tbody>')
    html.append('</table></div>')

    # Movement Table with Cell Highlighting
    html.append('<div class="table-section"><h2>Movement Metrics</h2><table id="movement_metrics">')
    html.append('<thead><tr>' + ''.join(f'<th data-type="{"numeric" if c != "stockcode" else "string"}">{c}</th>' for c in df_move.columns) + '</tr></thead>')
    html.append('<tbody>')
    for _, r in df_move.iterrows():
        stockcode = r['stockcode'].upper().strip()
        is_matched = stockcode in matched_stockcodes
        html.append(f'<tr>')
        for idx, c in enumerate(df_move.columns):
            if c == 'stockcode':
                cell_classes = []
                if stockcode in high_value_stocks:
                    cell_classes.append('high_value')
                cell_class = ' '.join(cell_classes)
            elif idx == 1 and is_matched:  # Second column (pe_point)
                cell_class = 'recent_match'
            else:
                cell_class = ''
                if c in ['current % ', 'premium %'] and not np.isnan(r['current % ']) and not np.isnan(
                        r['premium %']) and r['current % '] > r['premium %'] + 0.25:
                    cell_class = 'highlight_cell_move'
                elif c == 'left ce (%)' and r['ce_point'] != 0 and not np.isnan(r[c]) and r[c] < 0.5:
                    cell_class = 'highlight_cell_move'
            value = f'{r[c]:.2f}' if isinstance(r[c], float) else r[c]
            total_current_pct = df_move['current % '].sum()
            total_premium_pct = df_move['premium %'].sum()
            total_stock_chg = df_move['stock_chg_%'].sum()

            num_records = len(df_move)
            avg_stock_chg = total_stock_chg / num_records if num_records > 0 else 0
            move_footer = {col: 'TOTAL' if col == 'stockcode' else (
                f'{total_current_pct:.2f}' if col == 'current % ' else
                f'{total_premium_pct:.2f}' if col == 'premium %' else
                f'{avg_stock_chg:.2f}' if col == 'stock_chg_%' else ''
            ) for col in df_move.columns}

            html.append(f'<td class="{cell_class}">{value}</td>')
        html.append('</tr>')
    html.append('</tbody>')
    html.append('<tfoot><tr class="total">' + ''.join(
        f'<td>{move_footer[c]}</td>' for c in df_move.columns) + '</tr></tfoot>')
    html.append('</table></div>')

    # Watchlist Stocks Not in Positions
    html.append(
        '<div class="table-section"><h2>Current Market Data for Watchlist Stocks Not in Positions</h2><table id="watchlist_not_positions">')
    html.append('<thead><tr>' + ''.join(f'<th data-type="{"numeric" if c != "stockcode" and c != "Stock Classification" else "string"}">{c}</th>' for c in not_in_main_df.columns) + '</tr></thead>')
    html.append('<tbody>')
    for _, r in not_in_main_df.iterrows():
        stockcode = r['stockcode'].upper().strip()
        is_matched = stockcode in matched_stockcodes
        html.append(f'<tr>')
        for idx, c in enumerate(not_in_main_df.columns):
            if c == 'stockcode':
                cell_classes = []
                if stockcode in high_value_stocks:
                    cell_classes.append('high_value')
                cell_class = ' '.join(cell_classes)
            elif idx == 1 and is_matched:  # Second column (current_price)
                cell_class = 'recent_match'
            else:
                cell_class = ''
            value = f'{r[c]:.2f}' if isinstance(r[c], float) else r[c]
            html.append(f'<td class="{cell_class}">{value}</td>')
        html.append('</tr>')
    html.append('</tbody>')
    html.append('</table></div>')

    html.append('</body></html>')
    try:
        with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
            f.write(''.join(html))
        print(f"✅ Generated {OUTPUT_HTML}")
    except Exception as e:
        print(f"Error writing HTML file: {e}")

if __name__ == '__main__':
    main()


'''
#E6F0FA - Very Light Blue (similar to "Alice Blue")
#F0FFF0 - Honeydew (very light green)
#FFF9E6 - Very Light Yellow (similar to "Cornsilk")
#F5F5F5 - Whitesmoke (very light gray)
#E0FFFF - Light Cyan (very light turquoise)
'''
