import subprocess
from typing import Optional, Union

import dearpygui.dearpygui as dpg

import analysis_api

Id = Union[int, str]


def start() -> Id:
    input_text_box_id: Id
    mimic_text_id: Id
    loading_icon_id: Id
    table_id: Id
    repo: Optional[analysis_api.ClonedRepo] = None
    data_tab_bar: Id

    def on_input_text_enter(_, app_data, _user_data):
        dpg.show_item(loading_icon_id)
        is_valid = subprocess.run(['git', 'ls-remote', app_data],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        dpg.hide_item(loading_icon_id)
        if is_valid:
            dpg.set_value(mimic_text_id, "Valid")
            fill_table(app_data)
        else:
            dpg.set_value(mimic_text_id, "Invalid")

    def sort_callback(tbl, sort_specs):
        if sort_specs is None:
            return
        sort_specs = [(dpg.get_item_label(x), y == 1) for x, y in sort_specs]
        [sort, ascending] = zip(*sort_specs)
        tab = dpg.get_item_parent(tbl)
        file_path = dpg.get_item_user_data(tab)
        [_, file_name] = file_path.rsplit('\\', 1)
        per_file = repo.analyze_files(
            file_filter=lambda df: df[df.file_name == file_name],
            sort=sort,
            ascending=ascending,
        )
        df = per_file[file_path]
        write_table(tbl, df)

    def fill_table(url: str):
        nonlocal repo, data_tab_bar
        repo = analysis_api.ClonedRepo.from_url(url)
        per_file = repo.analyze_files()

        dpg.delete_item(data_tab_bar, children_only=True)
        for file, df in per_file.items():
            if df.empty:
                continue
            [_, file_name] = file.rsplit('\\', 1)

            with dpg.tab(label=f"{file_name}", parent=data_tab_bar, user_data=file):
                with dpg.table(callback=sort_callback, sortable=True, sort_multi=True) as tbl:
                    write_table(tbl, df)

    def write_table(table_id, df):
        dpg.delete_item(table_id, children_only=True)
        [nrows, ncols, *_] = df.shape
        for i in range(ncols):
            prefer_ascending = i != 0
            dpg.add_table_column(label=df.columns[i], default_sort=False,
                                 parent=table_id,
                                 prefer_sort_ascending=prefer_ascending,
                                 prefer_sort_descending=not prefer_ascending)
        for i in range(nrows):
            with dpg.table_row(parent=table_id):
                for j in range(ncols):
                    text = df.iloc[i, j]
                    text = "None" if text == "nan" else text
                    dpg.add_text(f"{text}")

    with dpg.window(label='Cyclomatic Complexity Analyzer', width=800, height=800, pos=(100, 100)) as ret:
        mimic_text_id = dpg.add_text(default_value="Fill in the text box")
        with dpg.group(horizontal=True):
            input_text_box_id = dpg.add_input_text(hint="Enter your repository URL, then press Enter",
                                                   callback=on_input_text_enter, on_enter=True)
            loading_icon_id = dpg.add_loading_indicator(style=1, color=(0, 0, 0, 255), show=False)
        data_tab_bar = dpg.add_tab_bar()

    return ret


def main():
    dpg.create_context()
    dpg.create_viewport(title='Custom Title', width=600, height=600)

    window_id = start()

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window(window_id, True)
    dpg.start_dearpygui()
    dpg.destroy_context()


main()
