import abc

import git

import features
import lizard
from git.repo.base import Repo
import glob
import os
import pandas as pd
from pathlib import Path
import shutil
import stat
from typing import Callable


class ClonedRepo:
    def __init__(self, root_path: Path, user_name: str, repo_name: str):
        self.root_path = root_path
        self.user_name = user_name
        self.repo_name = repo_name
        self.repo_analysis: pd.DataFrame = None
        self.file_analysis: dict[str, pd.DataFrame] = None

    @staticmethod
    def from_url(url: str) -> "ClonedRepo":
        return clone_repo(url)

    def analyze_files(self, file_filter: Callable[[pd.DataFrame], pd.DataFrame] = None, func_filter: Callable[[pd.DataFrame], pd.DataFrame] = None, sort: list[str] = None,
                      ascending: bool = True) -> dict[str, pd.DataFrame]:
        if self.file_analysis is None:
            self.perform_analysis()
        files_to_include = self.repo_analysis
        if file_filter is not None:
            files_to_include = file_filter(files_to_include)
        files_to_include = files_to_include.file_dir + '\\' + files_to_include.file_name
        if func_filter is None:
            func_filter = lambda x: x == x
        if sort is not None:
            sorter = lambda x: x.sort_values(by=sort, ascending=ascending)
        else:
            sorter = lambda x: x
        return {
            file: sorter(funcs[func_filter(funcs)])
            for file, funcs in self.file_analysis.items()
            if any(x == file for x in files_to_include)
        }

    def analyze_repo(self, file_filter: Callable[[pd.DataFrame], pd.DataFrame] = None, sort: list[str] = None, ascending: bool = True) -> pd.DataFrame:
        if self.repo_analysis is None:
            self.perform_analysis()
        files_to_include = self.repo_analysis
        if file_filter is not None:
            files_to_include = file_filter(files_to_include)
        if sort is not None:
            files_to_include = files_to_include.sort_values(by=sort, ascending=ascending)
        return files_to_include

    def perform_analysis(self):
        file_name_prefix_len = len(str(self.root_path))
        files = glob.glob(str(self.root_path / "**" / "*.py"))
        self.file_analysis = dict()
        files_data = []
        for file in files:
            name = file.split('/')[-1][:-3]
            if name == '__init__':
                continue
            lizard_analysis = lizard.analyze_file(file)
            extra_analysis: features.SourceFile = features.analyze_file(file)
            extra_functions = extra_analysis.functions
            flatten_nested_functions(extra_functions)
            extra_analysis: dict[tuple[str, int], features.Function] = {
                (func.name, func.start_line): func
                for func in extra_functions
            }
            functions = []
            for func in lizard_analysis.function_list:
                key = (func.name, func.start_line)
                extra = extra_analysis[key]
                functions.append({
                    'name': func.name,
                    'start_line': func.start_line,
                    'nloc': func.nloc,
                    'CCN': func.cyclomatic_complexity,
                    'enclosing_class': extra.enclosing_class,
                    'max_depth': extra.max_depth,
                    'branches': extra.branches,
                    'calls': extra.calls,
                    'returns': extra.returns,
                    'raises': extra.raises,
                    'assertions': extra.assertions,
                })

            df = pd.DataFrame(data=functions,
                              columns=['name', 'start_line', 'nloc', 'CCN', 'enclosing_class', 'max_depth', 'branches',
                                       'calls', 'returns', 'raises', 'assertions'])
            pretty_file_name = file[file_name_prefix_len:]
            self.file_analysis[pretty_file_name] = df
            if '\\' in pretty_file_name:
                [file_dir, file_name] = pretty_file_name.rsplit('\\', 1)
            else:
                [file_dir, file_name] = pretty_file_name.rsplit('/', 1)
            files_data.append({
                'file_dir': file_dir,
                'file_name': file_name,
                'nloc': lizard_analysis.nloc,
                'CCN': lizard_analysis.CCN,
                'func_token': lizard_analysis.token_count,
            })
        self.repo_analysis = pd.DataFrame(data=files_data,
                                          columns=['file_dir', 'file_name', 'nloc', 'CCN', 'func_token'])
        try:
            remove_dir(self.root_path)
        finally:
            pass


def clone_repo(url: str) -> ClonedRepo:
    """
    :param url: The URL of the repository that should be cloned
    :return: The path to the root of the local copy of the repository
    """
    [user_name, repo_name] = url.rsplit('/', 2)[1:]
    working_dir = Path(os.getcwd())
    temp_dir = working_dir / "tmp" / user_name / repo_name
    try:
        Repo.clone_from(url, temp_dir)
    except git.GitCommandError as err:
        if 'exists' in str(err):
            remove_dir(temp_dir)
            Repo.clone_from(url, temp_dir)
        else:
            raise err
    return ClonedRepo(temp_dir, user_name, repo_name)


def flatten_nested_functions(funcs: list[features.Function]):
    i = 0
    while i < len(funcs):
        func = funcs[i]
        for nested_func in func.nested_funcs:
            nested_func.name = f"{func.name}.{nested_func.name}"
            funcs.append(nested_func)
        func.nested_funcs.clear()
        i += 1


def remove_dir(path):
    shutil.rmtree(path, onerror=remove_readonly)


def remove_readonly(f, path, _):
    os.chmod(path, stat.S_IWRITE)
    f(path)
