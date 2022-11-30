import glob
import os
import shutil
import stat
from pathlib import Path
from typing import Callable, Iterable, Union

import git
import lizard
import pandas as pd
from git.repo.base import Repo

import features


class ClonedRepo:
    """A repository that was cloned to the local file system. It will be lazily
    analyzed and deleted once analysis is complete. The results of analysis are
    cached for repeated use.

    :field root_path: The relative or absolute path to the root of the local copy of the repository
    :field user_name: The name of the user who created the repository, if any
    :field repo_name: The name of the repository, if any
    """
    def __init__(self, root_path: Path, user_name: str, repo_name: str):
        self.root_path = root_path
        self.user_name = user_name
        self.repo_name = repo_name
        self.repo_analysis: pd.DataFrame = None
        self.file_analysis: dict[str, pd.DataFrame] = None

    @staticmethod
    def from_url(url: str) -> "ClonedRepo":
        """Creates a new `ClonedRepo` from the repository at the given URL.

        :param url: The URL of the repository
        :return: A `ClonedRepo` instance for the repository at `url`.
        :raise git.GitCommandError: if the URL is not the root of a valid
            git repository.
        """
        return clone_repo(url)

    def analyze_files(self, file_filter: Callable[[pd.DataFrame], pd.DataFrame] = None,
                      func_filter: Callable[[pd.DataFrame], pd.DataFrame] = None, sort: list[str] = None,
                      ascending: Union[bool, Iterable[bool]] = None) -> dict[str, pd.DataFrame]:
        """Analyze every code file in the repository, collecting statistics on each function according to the
        parameters.
        :param file_filter: A callback that filters out unwanted files
        :param func_filter: A callback that filters out unwanted functions in each file
        :param sort: A list of keys to sort the functions by
        :param ascending: If the functions in each file should be sorted (according to `sort`) in ascending order.
            If `sort` is `None`, then this is ignored
        :return: A mapping of file path to data for each function in that file
        """
        if self.file_analysis is None:
            self._perform_analysis()
        files_to_include = self.repo_analysis
        if file_filter is not None:
            # Filter out files, if necessary
            files_to_include = file_filter(files_to_include)

        # Use the files' full paths as keys in the dataframe
        files_to_include = files_to_include.file_dir + '\\' + files_to_include.file_name
        if func_filter is None:
            # The identity map will not filter out any functions
            func_filter = lambda x: x == x
        if sort is not None:
            # Sort the functions in each file
            if ascending is None:
                # Default is to sort ascending
                ascending = [True for _ in sort]
            sorter = lambda x: x.sort_values(by=list(sort), ascending=list(ascending))
        else:
            # By default, no sorting is performed
            sorter = lambda x: x

        # This looks kind of strange because of `DataFrame`'s operator overloads
        return {
            file: sorter(funcs[func_filter(funcs)])
            for file, funcs in self.file_analysis.items()
            if any(x == file for x in files_to_include)  # Only include files that were not filtered out
        }

    def analyze_repo(self, file_filter: Callable[[pd.DataFrame], pd.DataFrame] = None, sort: list[str] = None,
                     ascending: Union[bool, Iterable[bool]] = None) -> pd.DataFrame:
        """Analyzes every code file in the repository, collecting summary statistics on each file according to the
        parameters.

        :param file_filter: A callback that filters out unwanted files
        :param sort: A list of keys to sort the files by
        :param ascending: True if the files should be sorted (according to `sort`) in ascending order.
            If `sort` is `None`, then this is ignored
        :return: A Pandas DataFrame containing statistics for every remaining code file in the repository
        """
        if self.repo_analysis is None:
            self._perform_analysis()
        files_to_include = self.repo_analysis
        if file_filter is not None:
            files_to_include = file_filter(files_to_include)
        if sort is not None:
            if ascending is None:
                ascending = [True for _ in sort]
            files_to_include = files_to_include.sort_values(by=list(sort), ascending=ascending)
        return files_to_include

    def _perform_analysis(self):
        """The internal mechanism by which code analysis is performed"""
        file_name_prefix_len = len(str(self.root_path))
        # For now, it is hard-coded that only Python files are analyzed.
        files = glob.glob(str(self.root_path / "**" / "*.py"))
        self.file_analysis = dict()
        files_data = []
        for file in files:
            # Gets the name of the file without the '.py' extension
            name = file.split('/')[-1][:-3]
            # Remove __init__ files as they tend to throw off statistics
            if name == '__init__':
                continue
            lizard_analysis = lizard.analyze_file(file)
            extra_analysis: features.SourceFile = features.analyze_file(file)
            extra_functions = extra_analysis.functions
            flatten_nested_functions(extra_functions)
            # Since several functions in different classes can have the same name,
            # we use the start line as a secondary key.
            extra_analysis: dict[tuple[str, int], features.Function] = {
                (func.name, func.start_line): func
                for func in extra_functions
            }
            functions = []
            for func in lizard_analysis.function_list:
                key = (func.name, func.start_line)
                # A missing function has never been observed but best to keep this in just in case.
                extra = extra_analysis.get(key, features.Function('<missing>', -1, -1, None))
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
        _remove_dir(self.root_path)


def clone_repo(url: str) -> ClonedRepo:
    """
    :param url: The URL of the repository that should be cloned
    :return: The path to the root of the local copy of the repository
    """
    [user_name, repo_name] = url.rsplit('/', 2)[1:]
    working_dir = Path(os.getcwd())
    temp_dir = working_dir / "tmp" / f"{user_name}_{repo_name}"
    try:
        Repo.clone_from(url, temp_dir)
    except git.GitCommandError as err:
        # GitCommandError can be raised for several reasons, one is that the repository already
        # exists in the temp directory. In that case, we ignore the error, delete that part of
        # the temp directory, and try again.
        if 'exists' in str(err):
            _remove_dir(temp_dir)
            Repo.clone_from(url, temp_dir)
        else:
            raise err
    return ClonedRepo(temp_dir, user_name, repo_name)


def flatten_nested_functions(funcs: list[features.Function]):
    """Recursively flattens a list of (possibly nested) functions
    in-place and renames nested functions with fully-qualified names.

    For example, if the function `inner` is nested inside the function
    `do_stuff`, its fully-qualified name is `do_stuff.inner`.
    """
    i = 0
    while i < len(funcs):
        func = funcs[i]
        for nested_func in func.nested_funcs:
            nested_func.name = f"{func.name}.{nested_func.name}"
            funcs.append(nested_func)
        func.nested_funcs.clear()
        i += 1


def _remove_dir(path):
    shutil.rmtree(path, onerror=_remove_readonly)


def _remove_readonly(f, path, _):
    os.chmod(path, stat.S_IWRITE)
    f(path)
