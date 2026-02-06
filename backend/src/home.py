from flask import Blueprint, render_template, redirect
from logging import getLogger


home = Blueprint('home', __name__)
logger = getLogger("LOGGER")


@home.route('/index', methods=['GET'])
@home.route('/home', methods=['GET'])
@home.route('/', methods=['GET'])
def index():
    return render_template("home.html")

@home.route('/about', methods=['GET'])
def about():
    return render_template("about.html")
