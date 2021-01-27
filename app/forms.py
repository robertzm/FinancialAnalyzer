from flask_wtf import Form
from flask_wtf.file import FileField
from wtforms import SubmitField, SelectField


class UploadFileForm(Form):
    card = SelectField('card', choices=[("ChaseFreedom", "ChaseFreedom"),
                                        ("ChaseSapphire", "ChaseSapphire"),
                                        ("ChaseChecking", "ChaseChecking"),
                                        ("BoaChecking", "BoadChecking"),
                                        ("CitiPremier", "CitiPremier"),
                                        ("AmExSkymiles", "AmExSkymiles"),
                                        ("Unknown", "Unknown")])
    year = SelectField('year', choices=[("2021", "2021"),
                                        ("2020", "2020"),
                                        ("2019", "2019"),
                                        ("2018", "2018")])
    month = SelectField('month', choices=[("01", "01"), ("02", "02"), ("03", "03"), ("04", "04"),
                                          ("05", "05"), ("06", "06"), ("07", "07"), ("08", "08"),
                                          ("09", "09"), ("10", "10"), ("11", "11"), ("12", "12")])
    owner = SelectField('owner', choices=[('Kimi', 'Kimi'), ('Ying', 'Ying')])
    file = FileField()
    submit = SubmitField('submit')
