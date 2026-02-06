"""
Traditional Username/Password Authentication

This module handles traditional authentication with username and password.
Part of the modular StudentVC authentication system.
"""

from flask import render_template, request, flash, redirect, url_for, current_app, session
from ..models import User
from logging import getLogger
from datetime import timedelta
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
import secrets
from .. import db
from . import auth

logger = getLogger("LOGGER")


@auth.route('/login', methods=['GET', 'POST'])
def login():
    # Generate CSRF token if needed
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
        logger.debug(f"Generated new CSRF token: {session['csrf_token']}")
        
    # If already logged in, redirect to home
    if current_user.is_authenticated:
        logger.debug(f"Already logged in {current_user.name}, redirecting home")
        next_page = request.args.get('next') or request.form.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('home.index'))

    # handle first page request
    if request.method == 'GET':
        logger.info(f"GET request for login page")
        # Use new VC-enabled login page
        return render_template("login_vc.html")

    # handle form submission
    # get form data
    try:
        name = request.form.get('name')
        password = request.form.get('password')
        csrf_token = request.form.get('csrf_token')
        logger.info(f"Attempted Login: {name}")
        
        # Validate CSRF token
        if not csrf_token or csrf_token != session.get('csrf_token'):
            return login_error_handler("Invalid or missing CSRF token. Please try again.")
        
    except Exception as e:
        return login_error_handler(f"Invalid form {e}")

    # get user from db
    user = User.query.filter_by(name=name).first()

    # if user does not exist
    if user is None:
        return login_error_handler(f"User with name: {name} does not exist.")

    # if password is incorrect
    if not check_password_hash(user.password_hash, password):
        return login_error_handler(f"Password incorrect for {name}")

    login_user(user, remember=True, duration=timedelta(hours=1))
    flash('Logged in successfully!', category='success')
    logger.info(f"Login Success: {name}")
    
    # Redirect to next page if provided
    next_page = request.form.get('next') or request.args.get('next')
    if next_page and next_page.startswith('/'):
        return redirect(next_page)
    return redirect(url_for('home.index'))


def login_error_handler(log_error):
    errorString = "Invalid Credentials!"
    logger.error("LOGIN failed: " + log_error)
    flash(errorString, category='error')
    
    # Preserve the next parameter if present
    next_page = request.args.get('next')
    if next_page:
        return render_template("login_vc.html", next=next_page)
    return render_template("login_vc.html")


@auth.route('/logout')
@login_required
def logout():
    logger.info(f"Logout: {current_user.name}")
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    # if not in debug mode, redirect to home
    if not current_app.config['DEBUG']:
        logger.warning("Attempted to access register page in production")
        return redirect(url_for('home.index'))

    # if get then render the register page
    if request.method == 'GET':
        logger.info("GET request for register page")
        return render_template("register.html")

    try:
        name = request.form.get('name')
        password = request.form.get('password')
        logger.info(f"Attempted Register: {name}")
    except Exception as e:
        flash("Invalid form", category='error')
        return render_template("register.html")

    # check if user already exists
    existing_user = User.query.filter_by(name=name).first()
    if existing_user:
        flash("User already exists", category='error')
        return render_template("register.html")

    # create new user
    hashed_password = generate_password_hash(password)
    new_user = User(name=name, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    logger.info(f"Register Success: {name}")
    flash('Account created!', category='success')

    # login the user
    login_user(new_user, remember=True, duration=timedelta(hours=1))
    logger.info(f"Login Success: {name}")

    return redirect(url_for('home.index'))
