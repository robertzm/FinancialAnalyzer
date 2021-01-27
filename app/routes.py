from flask import current_app as app, make_response


@app.route("/", methods=["GET", "POST"])
def home():
    return make_response("routing done")