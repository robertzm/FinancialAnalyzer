import os

import uuid, shortuuid
from flask import current_app as app, make_response, request, flash, url_for, send_from_directory, render_template
from werkzeug.utils import redirect, secure_filename
import csv
from sqlalchemy import asc, desc

from app import db
from app.forms import UploadFileForm, AddRuleForm
from app.models import TransRecord, Rule


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
            filename = "_".join([card, year, month, owner, 'Transactions.csv'])
            path = os.path.join(app.config['BASE_FOLDER'], 'app', 'uploads', filename)
            try:
                file.save(path)
                parseAndSaveTransctions(card, owner, path)
            except ValueError as ve:
                return make_response(
                    "File parsing error, please check your uploading file type or card type: " + str(ve))
            except Exception as e:
                return make_response("Uploading filed failed, as: " + str(e))
            return redirect(url_for('list_records'))
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
        return redirect(url_for('list_records'))
    return render_template('home/addrule.html', form=form)


@app.route('/transactions', methods=['GET', 'POST'])
def list_records():
    baseQuery = TransRecord.query
    category = request.args.get('category')
    if category:
        baseQuery = baseQuery.filter(TransRecord.category == category).order_by(desc('date'))
    records = baseQuery.all()
    return render_template('home/transactions.html', records=records)


@app.route('/refresh', methods=['GET', 'POST'])
def refresh_records():
    rule = {}
    rules = Rule.query.all()
    for r in rules:
        rule[r.reference] = {'Category': r.category, 'FixedPayment': r.fixedPayment}

    records = TransRecord.query.all()
    for record in records:
        for key, value in rule.items():
            if (str(key)).upper() in (record.description).upper():
                record.category = value['Category']
                record.fixedPayment = value['FixedPayment']
                db.session.commit()
                break
    return redirect(url_for('list_records'))


@app.route('/uploads/<uuid>')
def uploaded_file(uuid):
    record = TransRecord.query.filter(TransRecord.uuid == uuid).first()
    if record:
        return send_from_directory(os.path.join(app.config['BASE_FOLDER'], 'app', 'uploads'), record.uploadfile)
    else:
        return make_response("no record, error!")


@app.route('/castfood/<uuid>')
def cast_food(uuid):
    record = TransRecord.query.filter(TransRecord.uuid == uuid).first()
    if record:
        record.category = "Restaurant"
        record.fixedPayment = False
        db.session.commit()
        return redirect(url_for('list_records', category="Unknown"))


def parseAndSaveTransctions(card, owner, filepath):
    rule = {}
    rules = Rule.query.all()
    for r in rules:
        rule[r.reference] = {'Category': r.category, 'FixedPayment': r.fixedPayment}

    try:
        if "Chase" in card:
            parseHelper(filepath, rule, owner, card, 'Description', 'Transaction Date')
        elif "Boa" in card:
            parseHelper(filepath, rule, owner, card, 'Payee', 'Posted Date')
        elif card == "Discover":
            parseHelper(filepath, rule, owner, card, 'Description', 'Trans. Date')
        elif "AmEx" in card:
            parseHelper(filepath, rule, owner, card, 'Description', 'Date')
        elif "Citi" in card:
            parseHelper(filepath, rule, owner, card, 'Description', 'Date')
    except Exception as e:
        raise (ValueError(e))


def parseHelper(filepath, rule, owner, card, descriptionName, dateName):
    with open(filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            timeslot = row[dateName][-4:] + "/" + row[dateName][:2]
            uid = shortuuid.encode(uuid.uuid1())
            category = "Unknown"
            fixed = False
            for key, value in rule.items():
                if (str(key)).upper() in (row[descriptionName]).upper():
                    category = value['Category']
                    fixed = value['FixedPayment']
                    break
            if 'Amount' in row.keys():
                amount = float(row['Amount'])
                if "Chase" in card or "Boa" in card:
                    gain = True if amount > 0 else False
                else:
                    gain = True if amount < 0 else False
            else:
                if row['Debit']:
                    amount = float(row['Debit'])
                    gain = False
                else:
                    amount = float(row['Credit'])
                    gain = True
            record = TransRecord(uuid=uid,
                                 timeslot=timeslot,
                                 owner=owner,
                                 card=card,
                                 date=row[dateName],
                                 description=row[descriptionName],
                                 category=category,
                                 fixedPayment=fixed,
                                 gain=gain,
                                 amount=abs(amount),
                                 uploadfile=os.path.basename(filepath))
            db.session.add(record)
            db.session.commit()
    return None
