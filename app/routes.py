import os

import uuid, shortuuid
from flask import current_app as app, make_response, request, flash, url_for, send_from_directory, render_template
from werkzeug.utils import redirect
from sqlalchemy import asc, desc
import pandas as pd
import math

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


@app.route('/editrecords', methods=['GET', 'POST'])
def edit_records():
    if request.method == 'POST':
        for uid in request.form.getlist('uuid'):
            r = TransRecord.query.filter(TransRecord.uuid == uid).first()
            r.category = request.form.getlist('category')[0]
            r.fixedPayment = True if bool(request.form.getlist('fixedpay')[0] == 'True') else False
            db.session.commit()
        return redirect(url_for('edit_records'))
    baseQuery = TransRecord.query
    category = request.args.get('Filter')
    if category:
        baseQuery = baseQuery.filter(TransRecord.category == category)
    records = baseQuery.order_by(asc('description')).all()
    return render_template('home/editrecords.html', records=records)


@app.route('/dash', methods=['GET', 'POST'])
def dashboard():
    from app.plotlyflask.dashboard import dash_url
    return render_template('home/dash.html', dash_url=dash_url)


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


# to be deprecated
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

    # df = pd.read_csv(filepath, parse_dates=['Transaction Date', 'Posting Date', 'Post Date', 'Date', 'Trans. Date'])

    try:
        if "Chase" in card:
            if "Checking" in card:
                df = pd.read_csv(filepath, parse_dates=['Posting Date'])
                df['Date'] = df['Posting Date'].dt.date
                df.drop(columns=['Details', 'Posting Date', 'Type', 'Balance', 'Check or Slip #', 'Empty'], inplace=True)
            else:
                df = pd.read_csv(filepath, parse_dates=['Transaction Date', 'Post Date'])
                df['Date'] = df['Transaction Date'].dt.date
                df.drop(columns=['Transaction Date', 'Post Date', 'Category', 'Type', 'Memo'], inplace=True)
        elif "Boa" in card:
            if "Checking" in card:
                df = pd.read_csv(filepath, parse_dates=['Posted Date'])
                df['Date'] = df['Posted Date'].dt.date
                df['Description'] = df['Payee']
                df.drop(columns=['Posted Date', 'Reference Number', 'Payee', 'Address'], inplace=True)
            else:
                df = pd.read_csv(filepath, parse_dates=['Posted Date'])
                df['Date'] = df['Posted Date'].dt.date
                df['Description'] = df['Payee']
                df.drop(columns=['Posted Date', 'Reference Number', 'Payee', 'Address'], inplace=True)
        elif card == "Discover":
            df = pd.read_csv(filepath, parse_dates=['Post Date', 'Trans. Date'])
            df['Date'] = df['Trans. Date'].dt.date
            df.drop(columns=['Trans. Date', 'Post Date', 'Category'], inplace=True)
            df['Amount'] = -1 * df['Amount']
        elif "AmEx" in card:
            df = pd.read_csv(filepath, parse_dates=['Date'])
            df['Date'] = df['Date'].dt.date
            df.drop(columns=['Receipt', 'Card Member', 'Account #'], inplace=True)
            df['Amount'] = -1 * df['Amount']
        elif "Citi" in card:
            df = pd.read_csv(filepath, parse_dates=['Date'])
            df['Date'] = df['Date'].dt.date
            for i in range(len(df['Credit'])):
                if math.isnan(df['Credit'].get(i)):
                    df['Credit'][i] = 0
            for i in range(len(df['Debit'])):
                if math.isnan(df['Debit'].get(i)):
                    df['Debit'][i] = 0
            df['Amount'] = -1 * (df['Credit'] + df['Debit'])
            df.drop(columns=['Status', 'Credit', 'Debit'], inplace=True)

        df = df.reindex(columns=['Date', 'Description', 'Amount'])
        parseHelper(df, rule, owner, card, filepath)
    except Exception as e:
        raise (ValueError(e))


def parseHelper(df, rule, owner, card, filepath):
    for row in df.values:
        timeslot = row[0].strftime("%Y/%m")  # row['Date'][-4:] + "/" + row['Date'][:2]
        uid = shortuuid.encode(uuid.uuid1())
        category = "Unknown"
        fixed = False
        for key, value in rule.items():
            if (str(key)).upper() in (row[1]).upper():
                category = value['Category']
                fixed = value['FixedPayment']
                break
        record = TransRecord(uuid=uid,
                             timeslot=timeslot,
                             owner=owner,
                             card=card,
                             date=row[0].strftime("%m/%d/%Y"),
                             description=row[1] if len(row[1]) <= 100 else row[1][:100],
                             category=category,
                             fixedPayment=fixed,
                             gain=True if row[2] > 0 else False,
                             amount=abs(row[2]),
                             uploadfile=os.path.basename(filepath))
        db.session.add(record)
        db.session.commit()
    return None
