import os

from flask import current_app as app, make_response, request, flash, url_for, send_from_directory, render_template
from werkzeug.utils import redirect, secure_filename

from app.forms import UploadFileForm


@app.route("/test", methods=["GET", "POST"])
def test():
    return make_response("routing done")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv'}

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    form = UploadFileForm()
    if form.validate_on_submit():
        card = form.card.data
        year = form.year.data
        month = form.month.data
        owner = form.owner.data
        file = form.file.data
        if not file or file.filename == '':
            return make_response("no file, error! ")
        if file and allowed_file(file.filename):
            filename = "_".join([card, year, month, owner, secure_filename(file.filename)])
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return make_response("saved files, correct")
    return render_template('home/uploadfile.html', title='Register', form=form)


@app.route('/test', methods=['GET', 'POST'])
def upload_file_devo():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

