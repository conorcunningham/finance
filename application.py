from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from models import *
from datetime import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Tell Flask what SQLAlchemy database to use.
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///finance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_row = User.query.filter_by(id=session["user_id"]).first()
    # holdings = db.session.query(Holdings, User).filter(User.id == user_row.id, Holdings.user == User.id).all()
    holdings = Holdings.query.filter_by(user=user_row.id).all()

    if holdings is not None:
        user_data = []

        value = float(user_row.cash)

        for row in holdings:
            share_data = {}
            share = lookup(row.symbol)
            share_data['symbol'] = share['symbol']
            share_data['name'] = share['name']
            share_data['price'] = share['price']
            share_data['qty'] = row.qty
            share_data['value'] = float(row.qty) * share['price']
            user_data.append(share_data)
            value += share_data['value']
            print(f"share: {share_data}")
            print(f"user: {user_data}")

        return render_template("index.html", data=user_data, value=value, cash=user_row.cash)
    else:
        return render_template("index.html", cash=user_row.cash)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    # display buy page for GET requests
    if request.method == "GET":
        return render_template("buy.html")

    if request.method == "POST":
        symbol = request.form.get("symbol")
        qty = request.form.get("shares")

        # check that symbol and qty aren't null
        if symbol is None:
            flash(f"Symbol {symbol} not found", "warning")
            return render_template("buy.html")

        if qty is None:
            flash(f"You must specify a quantity of shares to buy", "warning")
            return render_template("buy.html")

        # get the quote
        user_quote = lookup(symbol)
        qty = int(qty)

        # handle a return value of None
        if user_quote is None:
            flash(f"Symbol {symbol} not found", "warning")
            return render_template("buy.html")

        # get user's information
        user_row = User.query.filter_by(id=session["user_id"]).first()
        if user_row is None:
            print(session["user_id"])
            return apology("Something went very wrong, 400")

        # check the user can afford the purchase
        if user_row.cash < float(qty) * user_quote['price']:
            flash(f"Your balance is {user_row.cash} which is insufficient to purchase {qty} "
                  f"of {user_quote['symbol']}", "warning")
            return render_template("buy.html")

        user_row.cash = float(user_row.cash) - (float(qty) * user_quote['price'])

        # insert into holdings if holding doesn't exist, else update
        holding = Holdings.query.filter_by(user=session["user_id"], symbol=user_quote['symbol']).first()
        if holding is not None:
            holding.qty = qty
        else:
            holding = Holdings(user=session["user_id"], symbol=user_quote['symbol'], qty=qty)
            db.session.add(holding)

        # create an order record in orders
        order = Orders(user=session["user_id"], price=user_quote['price'],
                       symbol=user_quote['symbol'], qty=qty, timestamp=datetime.now())
        db.session.add(order)

        # add the symbol to symbols table if it doesn't exist
        holding = Symbols.query.filter_by(symbol=user_quote['symbol']).first()

        if holding is None:
            symbol = Symbols(symbol=user_quote['symbol'], name=user_quote['name'])
            db.session.add(symbol)

        # commit the db
        db.session.commit()

        return redirect(url_for('index'))


@app.route("/check/<name>", methods=["GET"])
def check(name):
    """Return true if username available, else false, in JSON format"""
    if name is None or len(name) < 1:
        return jsonify(False)

    available = User.query.filter_by(username=name).first()
    # if no result is returned to available, we know the username is available
    if available is None:
        return jsonify(True)
    else:
        return jsonify(False)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    order_history = Orders.query.filter_by(user=session['user_id']).all()

    # check to ensure we have a valid result
    if history is None:
        flash("You have no order history", "warning")
        return render_template("history.html")

    # this is what we'll return to render_template
    history_data = []

    for row in order_history:
        # order object as a dictionary
        order_data = {'symbol': row.symbol, 'qty': row.qty,
                      'timestamp': row.timestamp.strftime("%d/%m/%Y %H:%M:%S"), 'price': row.price}

        # append order object to history data
        history_data.append(order_data)

    return render_template("history.html", order=history_data)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        """
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))
        """
        username = request.form.get("username")
        rows = User.query.filter_by(username=username).all()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0].hash, request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0].id

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    # display quote template if request is GET
    if request.method == "GET":
        return render_template("quote.html")

    # get a quote for POST requests
    if request.method == "POST":
        symbol = request.form.get("symbol")

        # check that symbol isn't null
        if symbol is None:
            flash(f"Symbol {symbol} not found", "warning")
            return render_template("quote.html")

        # get the quote
        user_quote = lookup(symbol)

        # handle a return value of None
        if user_quote is None:
            flash(f"Symbol {symbol} not found", "warning")
            return render_template("quote.html")

        return render_template("quoted.html", quote=user_quote)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # display register page for GET requests
    if request.method == "GET":
        return render_template("register.html")

    # process form if POST request
    if request.method == 'POST':

        # get the user's details for sanity checking
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # check to ensure the user has provided input
        if not username or not password or not confirmation:
            return apology('Please ensure you fill our all required fields')

        # check that passwords match
        if password != confirmation:
            return apology('Please ensure your passwords match')

        # check that username is unique

        # insert user to database
        user_hash = generate_password_hash(password)
        user = User(username=username, hash=user_hash)
        db.session.add(user)
        db.session.commit()

        return render_template('login.html')


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "GET":
        # get a list of the users shares
        shares = Holdings.query.filter_by(user=session['user_id']).all()
        if shares is None:
            flash('You have no shares to sell')
            return render_template("sell.html")
        share_data = []
        for row in shares:
            share_data.append(row.symbol)
        return render_template("sell.html", data=share_data)

    if request.method == "POST":
        qty = int(request.form.get("shares"))
        symbol = request.form.get("symbol")

        if qty < 1 or symbol is None:
            return apology("There has been a problem", 400)

        # get share info
        share_info = lookup(symbol)

        # calculate earnings
        earnings = float(qty) * share_info['price']

        # update user's cash
        user = User.query.filter_by(id=session['user_id']).first()
        user.cash = float(user.cash) + earnings

        # update user's holding
        holdings = Holdings.query.filter_by(user=session['user_id'], symbol=symbol).first()
        holdings.qty = holdings.qty - qty

        # record a transaction
        order = Orders(user=session["user_id"], price=share_info['price'],
                       symbol=share_info['symbol'], qty=(-1 * qty), timestamp=datetime.now())
        db.session.add(order)

        # commi the changes
        db.session.commit()

        # return to index
        return redirect(url_for("index"))


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


def main():
    # Create tables based on each table definition in `models`
    db.create_all()
    db.session.commit()
    print(__name__)


if __name__ == "__main__":
    # Allows for command line interaction with Flask application
    with app.app_context():
        main()
