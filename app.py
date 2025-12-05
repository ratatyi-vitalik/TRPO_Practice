from flask import Flask, render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, UserMixin, logout_user, login_required, current_user
from datetime import date
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
bcrypt = Bcrypt(app)
app.secret_key = os.urandom(15)


class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(35), nullable=False)
    description = db.Column(db.String(100), nullable=False)
    text = db.Column(db.String(1000), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    type = db.Column(db.String(30), nullable=False)
    likes = db.Column(db.Integer, default=0)
    image_path = db.Column(db.String(50), nullable=False, unique=True)


class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    timetable = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(13), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == 'POST':
        hashed_password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        user = User(login=request.form['login'], email=request.form['phone_number'], password=hashed_password)
        try:
            db.session.add(user)
            db.session.commit()
            return redirect("/login")
        except Exception as e:
            print(e)
            return "Ошибка"
    return render_template('register.html')


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == 'POST':
        try:
            remember = request.form["remember"]
        except:
            remember = False
        user = User.query.filter_by(login=request.form["login"]).first()
        if user and bcrypt.check_password_hash(user.password, request.form["password"]):
            try:
                next_page = request.args["next"]
                login_user(user, remember=remember)
                return redirect(next_page)
            except:
                login_user(user, remember=remember)
                return redirect("/")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/")
def index():
    news = News.query.all()
    types = [i.type for i in News.query.all()]
    return render_template("index.html", types=types, news=news)


@app.route("/panel", methods=["POST", "GET"])
@login_required
def panel():
    types = [i.name for i in Section.query.all()]
    if request.method == "POST":
        if request.form["button"] == "create":
            file = request.files['image']
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new = News(title=request.form["title"],
                       description=request.form["description"],
                       text=request.form["text"],
                       date=date.today(),
                       type=request.form["type"],
                       image_path="static/uploads/" + filename)
            try:
                db.session.add(new)
                db.session.commit()
            except Exception as e:
                print(e)
                return "Ошибка"
        return render_template("panel.html", types=types)
    return render_template("panel.html", types=types)


@app.route("/timetable")
def timetable():
    return render_template("timetable.html")


if __name__ == "__main__":
    app.run(debug=True)