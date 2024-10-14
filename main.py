import flask
from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-goes-here'

# CREATE DATABASE

login_manager = LoginManager()
login_manager.init_app(app)

class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)
# CREATE TABLE IN DB


class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(1000))


with app.app_context():
    db.create_all()


@app.route('/')
def home():

    return render_template("index.html", logged_in=current_user.is_authenticated)


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        existing_user = db.session.execute(db.select(User).where(User.email == request.form.get("email")))
        if existing_user:
            flash("You've already signed up with that email, log in instead!")
        else:
            form_password = request.form.get("password")
            # split_pass = generate_password_hash(form_password, "pbkdf2:sha256:600000", 8).split(":")
            split_pass = generate_password_hash(form_password, "pbkdf2:sha256:600000", 8)
            # password = (split_pass[1] + split_pass[2])
            new_user = User(
                name=request.form.get("name"),
                email=request.form.get("email"),
                password=split_pass
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            # print(new_user.id)
            return redirect(url_for("secrets"))
    return render_template("register.html", logged_in=current_user.is_authenticated)


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_email = request.form.get("email")
        user_password = request.form.get("password")
        user_data = db.session.execute(db.select(User).where(User.email == user_email)).scalar()
        # print(user_data)
        if user_data:
            user_pass = check_password_hash(user_data.password, user_password)
            # print(user_pass)
            if user_pass:
                flash("Logged in Successfully", category="message")
                login_user(user_data)
                return redirect(url_for("secrets", name=user_data.name))
            else:
                flash("Sorry, wrong credentials")
        else:
            flash("Sorry, there's no account registered to this email", category="error")

    return render_template("login.html", logged_in=current_user.is_authenticated)


@app.route('/secrets')
@login_required
def secrets():

    # user_id = request.args.get("user_id")
    # print(user_id)
    # user = db.get_or_404(User, user_id)
    return render_template("secrets.html", name=current_user.name, logged_in=True)


@app.route('/logout')
@login_required
def logout():
    flash("You've successfully logged out")
    logout_user()
    return redirect(url_for("home"))


@app.route('/download')
@login_required
def download():
    return send_from_directory("static", path="files/cheat_sheet.pdf")



if __name__ == "__main__":
    app.run(debug=True)
