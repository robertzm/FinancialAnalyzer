from . import db

class TransRecord(db.Model):
    __tablename__ = "TransRecord"
    uuid = db.Column(db.String(64), primary_key=True, nullable=False)
    timeslot = db.Column(db.String(64), nullable=False)
    date = db.Column(db.String(64), default="01/01/1970", nullable=False)
    owner = db.Column(db.String(64), default="Kimi", nullable=False)
    card = db.Column(db.String(64), default="ChaseFreedom", nullable=False)
    description = db.Column(db.String(128), default="", nullable=False)
    category = db.Column(db.String(64), default="Unknown", nullable=False)
    fixedPayment = db.Column(db.Boolean, default=False)
    gain = db.Column(db.Boolean, default=False)
    amount = db.Column(db.Float, default=0, nullable=False)
    uploadfile = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return "<TransRecord {}".format(self.description + "-" + self.date)

class Rule(db.Model):
    __tablename__ = "Rule"
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(64), unique=True, nullable=False)
    category = db.Column(db.String(64), default="Unknown", nullable=False)
    fixedPayment = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return "<Rule {}".format(self.reference + "-" + self.category + "-" + self.fixedPayment)
