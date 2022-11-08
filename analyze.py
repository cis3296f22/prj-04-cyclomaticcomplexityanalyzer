import glob
import pandas as pd
import lizard
import os
import sqlalchemy.engine
import pymysql
import shutil
import yaml
import platform
import psutil
import json
from git.repo.base import Repo
from datetime import datetime
import joblib

# from sklearn.externals import joblib

with open('config.yml') as f:
    keys = yaml.load(f, Loader=yaml.FullLoader)

pymysql.install_as_MySQLdb()
j = 1
my = []
paths = None

# --------------------------------------------------------------------
URL = f"mysql+mysqlconnector://{keys['Keys']['DB_USER']}:{keys['Keys']['DB_PASSWORD']}@{keys['Keys']['DB_HOST']}:3306/{keys['Keys']['DB_NAME']}"
engine = sqlalchemy.create_engine(URL, echo=False)


def load(q, langs):
    if langs == "python":
        with open('/Users/yoonjaelee/PycharmProjects/Cyclomatic-Complexity-Analyzer/test/log.json', 'r') as f:
            json_data = json.load(f)
            if json_data is not None:
                for s in json_data:
                    if s not in my:
                        q.put(s)
                        my.append(s)


def queuing(lists, q, lang):
    global language
    language = lang
    for s in lists:
        if s not in my:
            q.put(s)
            my.append(s)
    print("Queue Size: " + str(q.qsize()))
    if lang == "python":
        with open('/Users/yoonjaelee/PycharmProjects/Cyclomatic-Complexity-Analyzer/test/log.json', 'w', encoding='utf-8') as file:
            json.dump(my, file, indent="\t")


def goes_through(q):
    while True:
        url = q.get()
        if url is not None:
            os.chdir("/Users/yoonjaelee/PycharmProjects/Cyclomatic-Complexity-Analyzer/test")
            user_name = url.rsplit('/', 2)[1]
            repo_name = url.rsplit('/', 1)[-1]
            temp_location = f"/Users/yoonjaelee/PycharmProjects/Cyclomatic-Complexity-Analyzer/test/{user_name}/{repo_name}"
            mother_direcotry = f"/Users/yoonjaelee/PycharmProjects/Cyclomatic-Complexity-Analyzer/test/{user_name}"
            Repo.clone_from(url, temp_location)
            df = calc_complexity(temp_location, language)
            if not df.empty:
                if language == "python":
                    make_df(df)
                    get_average(df, url, q)
                    #send(df)
                    my.remove(url)
                    with open('/Users/yoonjaelee/PycharmProjects/Cyclomatic-Complexity-Analyzer/test/log.json', 'w', encoding='utf-8') as file:
                        json.dump(my, file, indent='\t')
                    shutil.rmtree(mother_direcotry)
            else:
                print("no python files found in the repository")
                my.remove(url)
                with open('/Users/yoonjaelee/PycharmProjects/Cyclomatic-Complexity-Analyzer/test/log.json', 'w',
                          encoding='utf-8') as file:
                    json.dump(my, file, indent='\t')
                shutil.rmtree(mother_direcotry)



def make_df(df):
    nloc = df["nloc"].sum()
    loc = df["loc"].sum()
    CCN = df["CCN"].sum()
    func_token = df["func_token"].sum()
    df3 = pd.DataFrame(
        columns=["nloc", "loc", "CCN", "func_token"]
    )
    df3.loc[len(df)] = [nloc, loc, CCN, func_token]


def calc_complexity(url, lang):
    user_name = url.rsplit('/', 3)[1]
    repo_name = url.rsplit('/', 2)[1]
    full_name = f"{user_name}/{repo_name}"
    if lang == "python":
        path = url + "**/*.py"
    files = glob.glob(path, recursive=True)
    if lang == "python":
        df = pd.DataFrame(
            columns=["Repo_name", "file_dir", "file_name", "nloc", "loc", "CCN", "func_token"])
        if len(files) != 0:
            for i in files:
                code_name = i.split("/")
                name = code_name[len(code_name) - 1]
                if name != "__init__.py":
                    name = name.replace(".py", "")
                    f = open(i, "r", encoding='ISO-8859-1', errors='ignore')
                    mlb = lizard.analyze_file(i)
                    p = f.read()
                    dir_name = i.replace(os.getcwd(), '')  # split('/')[-1]
                    nloc = mlb.nloc
                    loc = len(p.split('\n'))
                    CCN = mlb.CCN
                    func_token = mlb.token_count
                    parsed_file = ""
                    df.update(df, overwrite=True)
                    df.loc[len(df)] = [full_name, i, name, nloc, loc, CCN, func_token]
    return df


def send(dataframe):
    dataframe.to_sql(name="initial", con=engine, if_exists='append', index=False)


def get_average(dataframe, path, q):
    user_name = path.rsplit('/', 2)[1]
    repo_name = path.rsplit('/', 1)[-1]
    df2 = pd.DataFrame(
        columns=["Time", "URL", "User_name", "Repo_name", "Total_File_Num", "Avg_nloc",
                 "Total_LOC",
                 "Avg_CCN",
                 "Max_CCN",
                 "Avg_func_token"]
    )
    avg_nloc = round(dataframe['nloc'].mean(), 2)
    total_loc = dataframe['loc'].sum()
    avg_ccn = round(dataframe['CCN'].mean(), 2)
    max_ccn = dataframe['CCN'].max()
    avg_token = round(dataframe['func_token'].mean(), 2)
    row_num = dataframe.shape[0]
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    df2.loc[len(df2)] = [timestamp, path, user_name, repo_name, row_num, avg_nloc, total_loc, avg_ccn,
                         max_ccn,
                         avg_token]
    if total_loc != 0:
        df2.to_sql(name='Repos', con=engine, if_exists='append', index=False)
        print(f"{user_name}/{repo_name} has been added to DB...... Updated Queue Size : {str(q.qsize())} ")
    else:
        print(f"Cannot fetch any files from {user_name}/{repo_name}..... Updated Queue Size : {str(q.qsize())}")
