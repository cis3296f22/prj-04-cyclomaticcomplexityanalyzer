import json
import yaml
import os
import sys
import time
import urllib.request
import pandas as pd
import pymysql
import requests
from flask import Flask, jsonify
from pandas.tseries.offsets import YearEnd

with open('config.yml') as f:
    keys = yaml.load(f, Loader=yaml.FullLoader)

# Github token
user = keys['Keys']['GITHUB_USER']
token = keys['Keys']['GITHUB_TOKEN']
app = Flask(__name__)

conn = None
cursor = None

try:
    conn = pymysql.connect(
        user=keys['Keys']['DB_USER'],
        password=keys['Keys']['DB_PASSWORD'],
        host=keys['Keys']['DB_HOST'],
        port=3306,
        db=keys['Keys']['DB_NAME'],
    )
    cursor = conn.cursor()
except pymysql.Error as e:
    print(f"Error connecting to MariaDB: {e}")
    sys.exit(1)


@app.route('/<string:language>/<int:stars>/<int:forks>/<int:years>/', methods=['GET'])
def to_scraper(language, stars, forks, years):
    for beg in pd.date_range(end=pd.datetime.now().date(), periods=years, freq='YS')[::-1]:
        dt = beg.strftime("%Y-%m-%d") + '..' + (beg + YearEnd(1)).strftime("%Y-%m-%d")
        url = f'https://api.github.com/search/repositories?q=stars:>={stars}+forks:>={forks}+language:{language}+created:{dt}+is:sponsorable+sort:reactions+sort:updated+&order=desc&per_page=100&'
        print(dt)

        crawling(url)

    return jsonify({"language": language, "forks": forks, "stars": stars, "years": years})


def scrape(url):
    listing = []
    response = requests.get(url)
    response_data = response.json()

    for s in response_data['items']:
        j = s['html_url']
        listing.append(j)

    urls = "http://127.0.0.1:5000/repos"
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    requests.post(urls, json=json.dumps(listing), headers=headers)


total_list = []
cursor.execute(f"SELECT URL FROM Repos")
db_url = [item[0] for item in cursor.fetchall()]
total_list.extend(db_url)

def crawling(url):
    requested = urllib.request.Request(url)
    response = urllib.request.urlopen(requested)
    rescode = response.getcode()
    tot_repos = requests.get(url, auth=(user, token)).json()
    total = tot_repos["total_count"]
    print('Total count of repos:', total)
    global total_list
    final_list = []
    i = 1
    while i <= (total / 100) + 1:
        final_url = url + 'page={}'.format(i)
        res = requests.get(final_url, auth=(user, token))
        repos = res.json()
        if rescode == 200:
            repos.get('items', 'error')
            repos = res.json()
            temp_list = ([i['html_url'] for i in repos['items']])
            for _ in repos['items']:
                try:
                    for res_data in temp_list:
                        if res_data in total_list:
                            continue
                        else:
                            final_list.append(res_data)
                            total_list.append(res_data)

                except KeyError:
                    print("error")

            i = i + 1
            temp_list.clear()
    urls = "http://127.0.0.1:5000/repos"
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    requests.post(urls, json=json.dumps(final_list), headers=headers)
    time.sleep(10)
    final_list.clear()


if __name__ == "__main__":
    app.run(host="127.0.0.1",
            port=4999,
            debug=True)
