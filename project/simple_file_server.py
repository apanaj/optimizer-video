from flask import Flask, send_file, request

app = Flask(__name__)


@app.route("/input.mp4")
def download_example():
    return send_file('input.mp4', as_attachment=True)


@app.route("/input.mkv")
def download_example_mkv():
    return send_file('input.mkv', as_attachment=True)


@app.route("/small.mp4")
def download_small_example():
    return send_file('small.mp4', as_attachment=True)


@app.route("/", methods=['POST'])
def webhook():
    print(request.json)
    return '', 200


@app.route("/v2/xcontent/webhook/", methods=['POST'])
def webhook2():
    print(request.json)
    return '', 202


if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')
