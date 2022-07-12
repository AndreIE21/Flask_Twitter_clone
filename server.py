from importlib.resources import path
from pyexpat.errors import messages
#from urllib.request import url
from flask import Flask, render_template, request, session, redirect, url_for
from platformdirs import user_cache_dir
from sqlalchemy import create_engine, delete
from werkzeug.security import generate_password_hash, check_password_hash




from urllib.request import Request, urlopen
from wtforms.validators import DataRequired



tweeter = Flask(__name__)
tweeter.config["SECRET_KEY"] = "this is not secret, remember, change it!"
engine = create_engine("sqlite:///tweeter.db")

@tweeter.route("/")
def index():
    tweets = []
    if "username" in session:
        query = f"""
        SELECT u.id, u.picture, u.username, t.tweet
        FROM tweets t
        INNER JOIN users u ON t.user_id=u.id
        INNER JOIN follows f ON f.followee_id=u.id
        WHERE f.follower_id={session['user_id']}
        """

        with engine.connect() as connection:
            tweets = connection.execute(query).fetchall()

    return render_template("index.html", tweets=tweets)

@tweeter.route("/register")
def register():
    return render_template("register.html")

@tweeter.route("/register", methods=["POST"])
def handle_register():
    username=request.form["username"]
    password=request.form["password"]
    picture=request.form["picture"]

    hashed_password = generate_password_hash(password)

    insert_query = f"""
    INSERT INTO users(username, picture, password)
    VALUES ('{username}', '{picture}', '{hashed_password}')
    """

    with engine.connect() as connection:
        connection.execute(insert_query)

        return redirect(url_for("index"))


@tweeter.route("/users")
def users():
    query = """
    SELECT id, username, picture
    FROM users
    """

    with engine.connect() as connection:
        users = connection.execute(query)

        return render_template("users.html", users=users)

@tweeter.route("/users/<user_id>")
def user_detail(user_id):
    query = f"""
    SELECT id, username, picture
    FROM users
    where id={user_id}
    """

    tweets_query = f"""
    SELECT tweet
    FROM tweets
    WHERE user_id={user_id}
    """

    with engine.connect() as connection:
        user = connection.execute(query).fetchone()
        tweets = connection.execute(tweets_query).fetchall()

        if user:
            return render_template("user_detail.html", user=user, tweets=tweets)
        else:
            return render_template("404.html"), 404

@tweeter.route("/login")
def login():
    return render_template("login.html")

@tweeter.route("/login", methods=["POST"])
def handle_login():
    username=request.form["username"]
    password=request.form["password"]

    login_query = f"""
    SELECT password, id
    FROM users
    WHERE username='{username}'
    """

    with engine.connect() as connection:
        user = connection.execute(login_query).fetchone()

        if user and check_password_hash(user[0], password):
            session["user_id"] = user[1]
            session["username"] = username
            return redirect(url_for("index"))
        else:
            return render_template("404.html"), 404

@tweeter.route("/logout")
def logout():
    session.pop("username")
    session.pop("user_id")

    return redirect(url_for("index"))


@tweeter.route("/tweet", methods=["POST"])
def handle_tweet():
    tweet=request.form["tweet"]

    insert_query = f"""
    INSERT INTO tweets(tweet, user_id)
    VALUES ('{tweet}', {session['user_id']})
    """

    with engine.connect() as connection:
        connection.execute(insert_query)

        return redirect(url_for("index"))

@tweeter.route("/follow/<followee>")
def follow(followee):
    if "user_id" not in session:
        return render_template("403.html"), 403    
    else:
        follower = session["user_id"]

        insert_query = f"""
        INSERT INTO follows(follower_id, followee_id)
        VALUES ({follower}, {followee})
        """

        with engine.connect() as connection:
            connection.execute(insert_query)

            return redirect(url_for("index", followee=followee))
#----------------------------------------------------------------------------------------------------

@tweeter.route("/message", methods=["POST"])
def handle_message():
    if "user_id" not in session:
        return render_template("404.html"), 404
    else:
        message=request.form["message"]
        sender_id = session['user_id']
        receiver_id = (request.form['receiver_id'])
        message_query = f"""
        INSERT INTO messages(text, from_id, to_id)
        VALUES ('{message}', '{sender_id}', '{receiver_id}')
        """

        with engine.connect() as connection:
            connection.execute(message_query)
            return redirect(url_for('send_message', user_id=receiver_id))



@tweeter.route("/messages")
def message_page():
    if "user_id" not in session:
        return render_template("403.html"), 403
    else: 
        messages_query = f"""
        SELECT m.from_id, u.username, u.picture, m.text, max(m.id)
        FROM messages m
        INNER JOIN users u ON m.from_id = u.id 
        WHERE m.to_id={session["user_id"]}
        GROUP BY m.from_id
        ORDER BY m.id DESC
        """

        with engine.connect() as connection:
            messages = connection.execute(messages_query).fetchall()
            return render_template("messages.html", messages=messages)

@tweeter.route("/messages/<user_id>")
def send_message(user_id):
    if "user_id" not in session:
        return render_template("403.html"), 403
    else: 
        query = f"""
        SELECT id, username, picture
        FROM users
        WHERE id={user_id}
        """
        received_messages = f"""
        SELECT m.from_id, u.username, u.picture, m.text 
        FROM messages m
        INNER JOIN users u ON m.from_id = u.id 
        WHERE (m.from_id={user_id} AND m.to_id={session["user_id"]}) OR 
        (m.to_id={user_id} AND m.from_id={session["user_id"]})
        ORDER BY m.id
        """

    with engine.connect() as connection:
        user = connection.execute(query).fetchone()
        messages = connection.execute(received_messages).fetchall()
        return render_template("send_message.html", user=user, messages = messages)

# Search function 
@tweeter.route('/search')
def search():
    return render_template("search.html")


@tweeter.route('/search', methods=["POST"])
def search2():
    tweets = []
    search = request.form["search"]
    search_query = f"""
    SELECT u.id, u.picture, u.username, t.tweet
    FROM tweets t
    INNER JOIN users u ON t.user_id=u.id
    WHERE T.TWEET LIKE '{"%" + search + "%"}' 
    Order by u.id
    """


    with engine.connect() as connection:
        tweets = connection.execute(search_query).fetchall()


        return render_template("search.html", tweets = tweets)





tweeter.run(debug=True)