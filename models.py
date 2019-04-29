from flask_sqlalchemy import SQLAlchemy

""" I'm already quite comfortable with SQL, and I feel that I have more to learn by using
    an ORM as I have little experience with this technique. I'm also currently taking CS50 Web
    and am working on my Django project. I have further plans to develop more with Django and hence
    I think the more experience I get with ORM the better it is for my overall education """

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, nullable=False)
    hash = db.Column(db.String, nullable=False)
    cash = db.Column(db.Numeric, nullable=False, default=10000)

    def __repr__(self):
        return "<User(ID='%i', username='%s', cash='%.2f')>" % (self.id, self.username, self.cash)


class Symbols(db.Model):
    __tablename__ = "symbols"
    symbol = db.Column(db.String, primary_key=True, nullable=False)
    name = db.Column(db.String, nullable=False)

    def __repr__(self):
        return "<Symbols(name='%s', symbol='%s')>" % (self.name, self.symbol)


class Orders(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    price = db.Column(db.Numeric, nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    symbol = db.Column(db.String, db.ForeignKey("symbols.symbol"), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return "<Orders(ID='%i', username='%s', symbol='%s', price='%.2f', timestamp='%s')>" % (
            self.id, self.user, self.symbol, self.price, self.timestamp)


class Holdings(db.Model):
    __tablename__ = "holdings"
    user = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True, nullable=False)
    symbol = db.Column(db.String, db.ForeignKey("symbols.symbol"), primary_key=True, nullable=False)
    qty = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return "<Holdings(username='%s', symbol='%s', qty='%i')>" % (self.user, self.symbol, self.qty)


db.Index('username', User.username, unique=True)
db.Index('symbol', Symbols.symbol, unique=True)
