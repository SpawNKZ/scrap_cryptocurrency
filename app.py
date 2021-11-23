from flask import Flask, request, jsonify, make_response, request, render_template, session, flash
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, redirect, url_for
from flask import request
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import requests
from requests import Session
import json
from transformers import pipeline


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:dias12345@localhost/Web'
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = 'f96aa0ad38be47c47982347a5b498743'

class Coin(db.Model):
    __tablename__ = 'coins'
    id = db.Column('id', db.Integer, primary_key=True)
    coin = db.Column('coin', db.Unicode)
    news = db.Column('news', db.Unicode)
    summary = db.Column('summary', db.Unicode)

    def __init__(self, coin, news, summary):
        self.coin = coin
        self.news = news
        self.summary = summary



class coinMarketCap:
    def newsParse(self, s):
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/info'
        x = s
        parameters = {
            'slug': x,
        }
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': '904da0b1-0e09-488a-ab1b-152351674dec'
        }

        session = Session()
        session.headers.update(headers)
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        a = data['data']
        id = list(a.keys())[0]
        for x in range(1, 6):
            url1 = 'https://api.coinmarketcap.com/content/v3/news?coins=' + id + '&page=' + str(x) + '&size=5'

            coin_html = requests.get(url1).json()
            subtitles = []
            num = 1 * ((x - 1) * 5 + 1)
            for coin in coin_html['data']:
                subtitles.append(coin['meta']['subtitle'])
                num = num + 1
            num += 5

        return subtitles

    def summary(self, subtitles):
        sumsum = []
        summarizer = pipeline("summarization")
        res = summarizer(subtitles, max_length=120, min_length=30, do_sample=False)
        for r in res:
            sumsum.append(r['summary_text'])

        return sumsum

@app.route('/coin', methods=["POST", "GET"])
def coin():
    if request.method == "POST":
        c = request.form['coin']
        data = Coin.query.filter_by(coin=c).first()
        if data:
            return redirect(url_for('crypto', crypto=c))
        scrap = coinMarketCap()
        n = scrap.newsParse(c)

        summ = scrap.summary(n)

        coin = Coin(coin=c, news=n, summary=summ)
        db.session.add(coin)
        db.session.commit()
        return redirect(url_for('crypto', crypto=c))

    else:
        return render_template("login.html")


@app.route('/coin/<crypto>', methods=["POST", "GET"])
def crypto(crypto):
    if request.method == "POST":
        c = request.form['coin']
        data = Coin.query.filter_by(coin=c).first()

        if data:
            new = str(data.news).replace('"', " ").replace("{", " ").replace("}", " ").replace("\\n", '')
            sumsumsum = str(data.summary).replace('"', " ").replace("{", " ").replace("}", " ")
            s = sumsumsum.split(' , ')
            l = new.split(' , ')
            return render_template("crypto.html", rev=zip(s, l), title=data.coin)

        scrap = coinMarketCap()
        n = scrap.newsParse(c)

        summ = scrap.summary(n)

        coin = Coin(coin=c, news=n, summary=summ)
        db.session.add(coin)
        db.session.commit()
        return redirect(url_for('crypto', crypto=c))

    coins = Coin.query.filter_by(coin=crypto).first()
    new = str(coins.news).replace('"', " ").replace("{", " ").replace("}", " ")
    sumsumsum = str(coins.summary).replace('"', " ").replace("{", " ").replace("}", " ")
    s = sumsumsum.split(' , ')
    l = new.split(' , ')
    return render_template("crypto.html", rev=zip(s, l), title=coins.coin)

def token_required(func):
    # decorator factory which invoks update_wrapper() method and passes decorated function as an argument
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.args.get('token')
        if not token:
            return jsonify({'Alert!': 'Token is missing!'}), 401

        try:

            data = jwt.decode(token, app.config['SECRET_KEY'])
        # You can use the JWT errors in exception
        # except jwt.InvalidTokenError:
        #     return 'Invalid token. Please log in again.'
        except:
            return jsonify({'Message': 'Invalid token'}), 403
        return func(*args, **kwargs)
    return decorated


@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return 'logged in currently'

# Just to show you that a public route is available for everyone


@app.route('/public')
def public():
    return 'For Public'

# auth only if you copy your token and paste it after /auth?query=XXXXXYour TokenXXXXX
# Hit enter and you will get the message below.


@app.route('/auth')
@token_required
def auth():
    return 'JWT is verified. Welcome to your dashboard !  '

# Login page


@app.route('/login', methods=['POST'])
def login():
    if request.form['username'] and request.form['password'] == '123456':
        session['logged_in'] = True

        token = jwt.encode({
            'user': request.form['username'],
            'expiration': str(datetime.utcnow() + timedelta(seconds=60))
        },
            app.config['SECRET_KEY'])
        return jsonify({'token': token})
    else:
        return make_response('Unable to verify', 403, {'WWW-Authenticate': 'Basic realm: "Authentication Failed "'})



if __name__ == "__main__":
    app.run(debug=True)
