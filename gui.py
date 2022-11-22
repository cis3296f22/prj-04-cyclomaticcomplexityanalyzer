import dataclasses
import enum
import math
import subprocess
from pathlib import Path
from typing import Optional, Union

import dearpygui.dearpygui as dpg
import numpy as np
import pandas as pd

import analysis_api

Id = Union[int, str]


class DataType(enum.Enum):
    NUMERIC = 1
    TEXT = 2


@dataclasses.dataclass()
class ColumnInfo:
    raw_name: str
    pretty_name: str
    tooltip: str
    dtype: DataType


DETAILS_COLUMNS = [
    ColumnInfo('name', 'Name', 'The name of the function, as it appears in the code', DataType.TEXT),
    ColumnInfo('start_line', 'Line', 'The line on which the function is defined', DataType.NUMERIC),
    ColumnInfo('nloc', '# Lines', 'The length of the function in lines of code', DataType.NUMERIC),
    ColumnInfo('CCN', 'CCN', 'The cyclomatic complexity number of the function', DataType.NUMERIC),
    ColumnInfo('enclosing_class', 'Class', 'The class in which the function is defined, if any', DataType.TEXT),
    ColumnInfo('max_depth', 'Max Depth', 'The greatest number of nested branches in the function', DataType.NUMERIC),
    ColumnInfo('branches', '# Branches', 'The number of branch points in the function', DataType.NUMERIC),
    ColumnInfo('calls', '# Calls', 'The number of function calls in the function', DataType.NUMERIC),
    ColumnInfo('returns', '# Returns', 'The number of `return` statements in the function', DataType.NUMERIC),
    ColumnInfo('raises', '# Raises', 'The number of `raise` statements in the function', DataType.NUMERIC),
    ColumnInfo('assertions', '# Asserts', 'The number of `assert` statements in the function', DataType.NUMERIC),
]
DETAILS_COLUMNS = {info.raw_name: info for info in DETAILS_COLUMNS}
PRETTY_DETAILS_COLUMNS = {v.pretty_name: v for v in DETAILS_COLUMNS.values()}

SUMMARY_COLUMNS = [
    ColumnInfo('file_dir', 'Path', 'The path from the root of the repository to the file', DataType.TEXT),
    ColumnInfo('file_name', 'Name', 'The name of the file', DataType.TEXT),
    ColumnInfo('nloc', '# Lines', 'The length of the file in lines of code', DataType.NUMERIC),
    ColumnInfo('CCN', 'CCN', 'The sum of the cyclomatic complexity numbers of all functions in the file',
               DataType.NUMERIC),
    ColumnInfo('func_token', '# Tokens', 'The number of individual tokens (keywords, identifiers, etc.) in the file',
               DataType.NUMERIC),
]
SUMMARY_COLUMNS = {info.raw_name: info for info in SUMMARY_COLUMNS}
PRETTY_SUMMARY_COLUMNS = {v.pretty_name: v for v in SUMMARY_COLUMNS.values()}


def start() -> Id:
    input_text_box_id: Id
    mimic_text_id: Id
    loading_icon_id: Id
    save_button_id: Id
    save_tooltip_id: Id
    repo: Optional[analysis_api.ClonedRepo] = None
    data_tab_bar: Id
    summary_tab: Id
    details_tab: Id

    def on_input_text_enter(_, app_data, _user_data):
        dpg.show_item(loading_icon_id)
        is_valid = subprocess.run(['git', 'ls-remote', app_data],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        dpg.hide_item(loading_icon_id)
        if is_valid:
            dpg.set_value(mimic_text_id, "Valid")
            fill_table(app_data)
            dpg.show_item(save_button_id)
            dpg.show_item(save_tooltip_id)
        else:
            dpg.set_value(mimic_text_id, "Invalid")

    def sort_details_callback(tbl, sort_specs):
        if sort_specs is None:
            return
        sort_specs = [(PRETTY_DETAILS_COLUMNS[dpg.get_item_label(x)].raw_name, y == 1) for x, y in sort_specs]
        [sort, ascending] = zip(*sort_specs)
        file_path = dpg.get_item_user_data(tbl)
        [_, file_name] = file_path.rsplit('\\', 1)
        per_file = repo.analyze_files(
            file_filter=lambda df: df[df.file_name == file_name],
            sort=sort,
            ascending=ascending,
        )
        df = per_file[file_path]
        write_table(tbl, df, DETAILS_COLUMNS)

    def sort_summary_callback(tbl, sort_specs):
        if sort_specs is None:
            return
        sort_specs = [(PRETTY_SUMMARY_COLUMNS[dpg.get_item_label(x)].raw_name, y == 1) for x, y in sort_specs]
        [sort, ascending] = zip(*sort_specs)
        repo_analysis = repo.analyze_repo(
            sort=sort,
            ascending=ascending,
        )
        write_table(tbl, repo_analysis, SUMMARY_COLUMNS)

    def fill_table(url: str):
        nonlocal repo, data_tab_bar
        repo = analysis_api.ClonedRepo.from_url(url)
        per_file = repo.analyze_files()
        repo_analysis = repo.analyze_repo()

        dpg.delete_item(data_tab_bar, children_only=True)
        dpg.delete_item(summary_tab, children_only=True)

        with dpg.table(parent=summary_tab, callback=sort_summary_callback, sortable=True, sort_multi=True) as tbl:
            write_table(tbl, repo_analysis, SUMMARY_COLUMNS)
        for file, df in per_file.items():
            if df.empty:
                continue
            [_, file_name] = file.rsplit('\\', 1)

            with dpg.tab(label=file_name, parent=data_tab_bar, user_data=file):
                with dpg.group(horizontal=False):
                    with dpg.table(callback=sort_details_callback, sortable=True, sort_multi=True,
                                   policy=dpg.mvTable_SizingStretchProp, user_data=file, scrollY=True,
                                   height=400, width=-1) as tbl:
                        write_table(tbl, df, DETAILS_COLUMNS)
                    X, Y = make_histogram_series(df)
                    title = "CCN Histogram"
                    # fix awkward scaling if CCN=1 greatly outweighs other values
                    if X[0] == 1 and Y[0] - max(Y[1:]) > 15:
                        X, Y = X[1:], Y[1:]
                        title += " (without CCN=1)"
                    with dpg.plot(label=title, height=-1, width=-1):
                        x_tag = f"{file}__x_axis"
                        y_tag = f"{file}__y_axis"

                        dpg.add_plot_axis(dpg.mvXAxis, label='CCN', tag=x_tag, no_gridlines=True)
                        x_max = int(np.max(X)) + 1
                        x_tick_step = math.ceil((x_max - 1) / 10)
                        dpg.set_axis_ticks(dpg.last_item(), tuple((str(x), x) for x in range(1, x_max, x_tick_step)))
                        dpg.set_axis_limits(x_tag, np.min(X) - 1, np.max(X) + 1)
                        dpg.add_plot_axis(dpg.mvYAxis, label='Count', tag=y_tag)

                        y_max = np.max(Y) + 1
                        y_tick_step = math.ceil((y_max - 1) / 4)
                        dpg.set_axis_ticks(dpg.last_item(), tuple((str(x), x) for x in range(0, y_max, y_tick_step)))
                        dpg.set_axis_limits(y_tag, 0, y_max)

                        dpg.add_bar_series(X, Y, parent=dpg.last_item(), weight=0.5)

    def make_histogram_series(df):
        uniq_values = len(df.groupby(['CCN']))
        num_bins = min(uniq_values, 8)
        labels = list(range(num_bins))
        bars, bins = pd.cut(df.get('CCN'), num_bins, labels=labels, retbins=True)
        bins = bins[:-1]
        bins[0] = math.ceil(bins[0])
        bins[-1] = math.ceil(bins[-1])
        bins = np.floor(bins)
        ret = [0] * num_bins
        for x in list(bars):
            ret[x] += 1
        return bins, ret

    def write_table(table_id, df, columns: dict[str, ColumnInfo]):
        dpg.delete_item(table_id, children_only=True)
        [nrows, ncols, *_] = df.shape
        for i in range(ncols):
            prefer_ascending = i <= 1
            column_info = columns[df.columns[i]]
            col_stretch = column_info.dtype == DataType.TEXT
            col = dpg.add_table_column(label=column_info.pretty_name, default_sort=False,
                                       parent=table_id,
                                       prefer_sort_ascending=prefer_ascending,
                                       prefer_sort_descending=not prefer_ascending,
                                       width_stretch=col_stretch,
                                       )
            with dpg.tooltip(col):
                dpg.add_text(column_info.tooltip)
        for i in range(nrows):
            with dpg.table_row(parent=table_id):
                for j in range(ncols):
                    text = str(df.iloc[i, j])
                    text = "None" if text == "nan" else text
                    dpg.add_text(f"{text}")

    def on_save_button_press(sender, app_data):
        dpg.show_item('save_dir_id')

    def on_save_dir_selected(sender, app_data):
        dpg.hide_item(sender)
        path = Path(app_data['file_path_name'])
        if not path.exists():
            path.mkdir()
        summary_path = path / 'summary.csv'
        repo.repo_analysis.to_csv(summary_path)
        details_dir = path / "details"
        print(details_dir)
        if not details_dir.exists():
            details_dir.mkdir()
        for file, df in repo.file_analysis.items():
            file_path = file.strip('\\/')
            parent_path = file_path.split('\\')[:-1]
            dir = details_dir
            for segment in parent_path:
                dir = dir / segment
                if not dir.exists():
                    dir.mkdir()
            csv_path = details_dir / f"{file_path}.csv"
            print(csv_path)
            df.to_csv(csv_path)

    dpg.add_file_dialog(directory_selector=True, show=False, tag='save_dir_id',
                        callback=on_save_dir_selected, width=400, height=400)

    with dpg.window(label='Cyclomatic Complexity Analyzer', width=800, height=800, pos=(100, 100)) as ret:
        mimic_text_id = dpg.add_text(default_value="Fill in the text box")
        with dpg.group(horizontal=True):
            input_text_box_id = dpg.add_input_text(hint="Enter your repository URL, then press Enter",
                                                   callback=on_input_text_enter, on_enter=True)
            save_button_id = dpg.add_button(label='Save', show=False, callback=on_save_button_press)
            loading_icon_id = dpg.add_loading_indicator(style=1, color=(0, 0, 0, 255), show=False)

            save_tooltip_id = dpg.add_tooltip(save_button_id, show=False)
            dpg.add_text('Save the raw data as a collection of CSV files', parent=save_tooltip_id)
        with dpg.tab_bar():
            summary_tab = dpg.add_tab(label='Summary')
            details_tab = dpg.add_tab(label='Details')
            data_tab_bar = dpg.add_tab_bar(parent=details_tab)

    return ret


def main():
    dpg.create_context()
    dpg.create_viewport(title='Cyclomatic Complexity Analyzer', width=600, height=600)

    window_id = start()

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window(window_id, True)
    dpg.start_dearpygui()
    dpg.destroy_context()


main()
