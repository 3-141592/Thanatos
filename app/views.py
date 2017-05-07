from flask import render_template,flash,redirect, session,url_for, request, g
from flask_login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from .forms import EditForm, SearchForm, SolutionForm
from .models import User, Challenge
from .oauth import OAuthSignIn
from datetime import datetime
from config import USER_PER_PAGE, MAX_SEARCH_RESULTS


@app.before_request
def before_request():

    g.user = current_user
    if g.user.is_authenticated:
        g.user.last_seen=datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()
        g.search_form = SearchForm()

@app.route('/',methods = ['GET','POST'])
@app.route('/index',methods = ['GET','POST'])
@app.route('/index/<int:page>',methods = ['GET','POST'])
@login_required
def index(page=1):
    user_list = User.query.paginate(page, USER_PER_PAGE, False)
    user = g.user
    challenges = user.get_unlocked_challenges().all()
    print challenges
    return render_template('index.html',title='Home',user= user, available=challenges,user_list=user_list)

@app.route('/search', methods = ['POST'])
@login_required
def search():
    if not g.search_form.validate_on_submit():
        return redirect(url_for('index'))
    return redirect(url_for('search_results', query=g.search_form.search.data))

@app.route('/search_results/<query>')
@login_required
def search_results(query):
    results = Challenge.query.whoosh_search(query, MAX_SEARCH_RESULTS).filter(Challenge.min_lvl <= g.user.level).all()
    return render_template('search_results.html',
                           query=query,
                           results=results)

@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()

@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email = oauth.callback()
    username=User.make_unique_nickname(username)
    if social_id is None:
        flash('Authentication failed')
        return redirect(url_for('index'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, nickname = username, email = email)
        db.session.add(user)
        db.session.commit()
        db.session.add(user.follow(user))
        db.session.commit()
    login_user(user, True)
    unlocked = Challenge.query.filter(Challenge.min_lvl <= user.level).all()
    for challenge in unlocked:
        user.unlocked.append(challenge)
    db.session.add(user)
    db.session.commit()
    return redirect(request.args.get('next') or url_for('index'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/edit',methods=['GET','POST'])
@login_required
def edit():
    form = EditForm(g.user.nickname)
    if form.validate_on_submit():
        g.user.nickname = form.nickname.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your Changes have been saved!')
        return redirect(url_for('edit'))
    else:
        form.nickname.data = g.user.nickname
        return render_template('edit.html', form = form )

@app.route('/user/<nickname>')
@login_required
def user(nickname):
    user = User.query.filter_by(nickname = nickname).first()
    if user == None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))
    return render_template('user.html', user = user)

@app.route('/follow/<nickname>')
@login_required
def follow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found' % nickname)
        return redirect(url_for('index'))
    # if user == g.user:
    #     flash("You can't follow yourself.")
    #     return redirect(url_for('user',nickname=nickname))
    u = g.user.follow(user)
    if u is None:
        flash('Cannot follow '+nickname+'.')
        return redirect(url_for('user',nickname = nickname))
    db.session.add(u)
    db.session.commit()
    flash("You're now following "+nickname+"!")
    return redirect(url_for('user', nickname = nickname))



@app.route('/unfollow/<nickname>')
@login_required
def unfollow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))
    if user == g.user:
        flash('You can\'t unfollow yourself!')
        return redirect(url_for('user', nickname=nickname))
    u = g.user.unfollow(user)
    if u is None:
        flash('Cannot unfollow ' + nickname + '.')
        return redirect(url_for('user', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash('You have stopped following ' + nickname + '.')
    return redirect(url_for('user', nickname=nickname))

@app.route('/challenge/<title>',methods = ['GET','POST'])
@login_required
def challenge(title):
    challenge = Challenge.query.filter(Challenge.title == title).first()
    form = SolutionForm()
    if form.validate_on_submit():
        if form.solution.data == challenge.solution:
            if not g.user.has_solved(challenge.id):
                g.user.add_solved(challenge)
            flash('Success!')
            return redirect(url_for('index'))
        else:
            flash('Wrong!')
            return render_template('challenge.html',challenge=challenge,form=form)
    else:
        if challenge is None:
            flash('Challenge not found')
            return redirect(url_for('index'))
        if g.user.level < challenge.min_lvl:
            flash('You need to be at least Level %d to acces this challenge' % challenge.min_lvl)
            return redirect(url_for('index'))


        return render_template('challenge.html',challenge=challenge,form=form)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'),404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))
