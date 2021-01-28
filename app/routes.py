import os

import uuid, shortuuid
from flask import current_app as app, make_response, request, flash, url_for, send_from_directory, render_template
from werkzeug.utils import redirect, secure_filename
import csv

from app import db
from app.forms import UploadFileForm, AddRuleForm
from app.models import TransRecord, Rule


@app.route("/test", methods=["GET", "POST"])
def test():
    return make_response("routing done")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'txt', 'csv'}


@app.route('/upload', methods=['GET', 'POST'])
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
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            parseAndSaveTransctions(year + "/" + month, card, owner, path)
            return make_response("saved files, correct")
    return render_template('home/uploadfile.html', form=form)


@app.route('/addrule', methods=['GET', 'POST'])
def add_rule():
    form = AddRuleForm()
    if form.validate_on_submit():
        reference = form.reference.data
        category = form.category.data
        fixedPayment = form.fixedPayment.data
        rule = Rule(reference=reference, category=category, fixedPayment=(fixedPayment == "True"))
        db.session.add(rule)
        db.session.commit()
        return make_response("added new rule successfully. ")
    return render_template('home/addrule.html', form=form)

@app.route('/transactions', methods=['GET', 'POST'])
def list_records():
    records = TransRecord.query.all()
    return render_template('home/transactions.html', records=records)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


def parseAndSaveTransctions(timeslot, card, owner, filepath):
    rule = {}
    rules = Rule.query.all()
    for r in rules:
        rule[r.reference] = {'Category': r.category, 'FixedPayment': r.fixedPayment}

    if card == "ChaseFreedom" or card == "ChaseSapphire" or card == "ChaseChecking":
        with open(filepath, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                uid = shortuuid.encode(uuid.uuid1())
                for key, value in rule.items():
                    if (str(key)).upper() in (row['Description']).upper():
                        category = value['Category']
                        fixed = value['FixedPayment']
                        break
                    else:
                        category = "Unknown"
                        fixed = False
                amount = float(row['Amount'])
                record = TransRecord(uuid=uid,
                                     timeslot=timeslot,
                                     owner=owner,
                                     card=card,
                                     date=row['Transaction Date'],
                                     description=row['Description'],
                                     category=category,
                                     fixedPayment=fixed,
                                     gain=True if amount > 0 else False,
                                     amount=abs(amount))
                db.session.add(record)
                db.session.commit()
    return None
