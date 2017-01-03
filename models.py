from app import db

class Message(db.Model):
    __tablename__ = 'message'
    def __init__(self):
        self.i = 1
    messageid = db.Column(db.Integer, primary_key=True)
    messagecontent = db.Column(db.String(255))
    fromid = db.Column(db.Integer)
    toid = db.Column(db.Integer)
    roomid = db.Column(db.Integer)
    createtime = db.Column(db.String(20))

    def __repr__(self):
        return '< %r>' % self.messagecontent