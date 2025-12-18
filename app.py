from flask import Flask, render_template, redirect, request, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, UserMixin, logout_user, login_required, current_user
from datetime import date
import os
from re import match

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
bcrypt = Bcrypt(app)
app.secret_key = os.urandom(15)

association_table = db.Table(
    'association',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('news_id', db.Integer, db.ForeignKey('news.id'))
)


class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(35), nullable=False)
    description = db.Column(db.String(100), nullable=False)
    text = db.Column(db.String(1000), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    type = db.Column(db.String(30), nullable=False)
    image_path = db.Column(db.String(50), nullable=False, unique=True)

    likes = db.relationship('User', secondary=association_table, back_populates='liked')


class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    teacher = db.Column(db.String(30), nullable=False)
    description = db.Column(db.Text, nullable=False)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(13), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20))

    liked = db.relationship('News', secondary=association_table, back_populates='likes')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == 'POST':
        login = request.form["login"]
        if User.query.filter_by(login=login).first():
            print(User.query.filter_by(login=login), login)
            flash("Это имя пользователя уже занято!", "error")
            return redirect("/register")
        email = request.form["email"]
        if User.query.filter_by(email=email).first():
            flash("Этот номер телефона уже зарегистрирован!", "error")
            return redirect("/register")
        pattern = r'^\+375 \d{2} \d{3} \d{2} \d{2}$'
        if not match(pattern, email):
            flash("Неверный формат номера телефона!", "error")
            return redirect("/register")
        hashed_password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        user = User(login=request.form['login'], email=request.form['email'], password=hashed_password)
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
        user = User.query.filter_by(login=request.form["login"]).first()
        if user and bcrypt.check_password_hash(user.password, request.form["password"]):
            try:
                next_page = request.args["next"]
                login_user(user)
                return redirect(next_page)
            except:
                login_user(user)
                return redirect("/")
        else:
            flash("Неверный логин или пароль!", "error")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/", methods=["POST", "GET"])
def index():
    news = News.query.all()
    types = [i.name for i in Section.query.all()]
    if request.method == "POST":
        if request.form["button"] == "pick":
            news = [i for i in news if i.type == request.form["type"]]
    page = 1
    max_page = int(len(news) / 10 + 0.9)
    if "page" in request.args:
        page = int(request.args["page"])
    news = news[(page - 1) * 10:(page - 1) * 10 + 10]
    sections = Section.query.all()
    return render_template("index.html", types=types, news=news, page=page, max_page=max_page, sections=sections)


@app.route("/panel", methods=["POST", "GET"])
@login_required
def panel():
    types = [i.name for i in Section.query.all()]
    news = News.query.all()
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
        return render_template("panel.html", types=types, news=news)
    return render_template("panel.html", types=types, news=news)


@app.route("/new", methods=["POST", "GET"])
def new():
    if not ("id" in request.args and request.args["id"].isdigit() and News.query.get(request.args["id"])):
        return "404"
    new = News.query.get(request.args["id"])
    try:
        liked = new in current_user.liked
    except:
        liked = False
    if request.method == "POST":
        if not current_user.is_authenticated:
            return redirect("/login")
        if liked:
            try:
                current_user.liked.remove(new)
                db.session.commit()
                liked = not liked
            except Exception as e:
                print(e)
                return "Ошибка"
        else:
            try:
                current_user.liked.append(new)
                db.session.commit()
                liked = not liked
            except Exception as e:
                print(e)
                return "Ошибка"
    return render_template("new.html", new=new, liked=liked, likes=len(new.likes))


if __name__ == "__main__":
    app.run(debug=True)
