import threading

from flask import Flask
from flask import request
import json
import queue
import analyze

app = Flask(__name__)

q = queue.Queue()


@app.route("/repos", methods=['GET', 'POST'])
def connect_python():
    analyze.load(q, "python")  #
    content = request.json
    contents = json.loads(content)
    analyze.queuing(contents, q, "python")

    return ""


if __name__ == "__main__":
    t = threading.Thread(target=analyze.goes_through, args=(q,))
    t.daemon = True
    t.start()

    app.run(host="127.0.0.1",
            port=5000,
            debug=True)

    q.join()
