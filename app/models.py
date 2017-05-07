from app import app, db,lm
from hashlib import md5
from datetime import datetime
import sys
if sys.version_info >= (3, 0):
    enable_search = False
else:
    enable_search = True
    import flask_whooshalchemy as whooshalchemy


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    social_id = db.Column(db.String(64), nullable = False, unique=True)
    nickname = db.Column(db.String(64),index = True, nullable = False)
    email = db.Column(db.String(120), index=True, nullable = True)
    is_mod = db.Column(db.Boolean,default=False)
    last_seen = db.Column(db.DateTime)
    stream_read = db.Column(db.DateTime)
    followed = db.relationship('User',secondary='followers',
    primaryjoin='(followers.c.follower_id == User.id)',
    secondaryjoin='(followers.c.followed_id == User.id)',
    backref = db.backref('followers', lazy = 'dynamic'),
    lazy = 'dynamic'
    )
    unlocked = db.relationship('Challenge',secondary='unlocked',backref = 'unlocked_by')

    level = db.Column(db.Integer,default=0)

    @staticmethod
    def make_unique_nickname(nickname):
        if User.query.filter_by(nickname=nickname).first() is None:
            return nickname
        version = 2
        while True:
            new_nickname = nickname + str(version)
            if User.query.filter_by(nickname=new_nickname).first() is None:
                break
            version += 1
        return new_nickname

    def avatar(self, size):
        email = "example@mail.com"
        if self.email is not None:
            email = str(self.email)
        return 'http://www.gravatar.com/avatar/%s?d=mm&s=%d' % (md5(email.encode('utf-8')).hexdigest(), size)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)
        except NameError:
            return str(self.id)

    def __repr__(self):
        return '<User %r>' % (self.nickname)

    def follow(self,user):
        if not self.is_following(user):
            self.followed.append(user)
            return self

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            return self

    def is_following(self,user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def get_solved_challenges(self):
        return Challenge.query.join(Solves,(Solves.solved_id == Challenge.id)).filter(Solves.solver_id == self.id).order_by(Solves.time.desc())

    def get_unlocked_challenges(self):
        return Challenge.query.join(unlocked,(unlocked.c.unlocked == Challenge.id)).filter(unlocked.c.user == self.id).order_by(Challenge.min_lvl.desc())

    def get_solved_number(self):
        return self.get_solved_challenges().count()

    def add_solved(self,challenge):
        solve = Solves(time = datetime.utcnow())
        solve.solved=challenge
        self.solves.append(solve)
        db.session.add(solve)
        db.session.add(self)
        db.session.commit()

    def has_solved(self,challenge_id):
        return self.get_solved_challenges().filter(Challenge.id == challenge_id).count() > 0


class Solves(db.Model):
    __tablename__ = 'solves'
    id = db.Column(db.Integer,primary_key=True)
    solver_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    solved_id = db.Column(db.Integer,db.ForeignKey('challenge.id'))
    time = db.Column(db.DateTime)

    solver = db.relationship('User', backref='solves')#,lazy='dynamic')
    solved = db.relationship('Challenge', backref = 'solves')#,lazy='dynamic')

followers = db.Table('followers',
db.Column('follower_id',db.Integer,db.ForeignKey('user.id')),
db.Column('followed_id',db.Integer, db.ForeignKey('user.id')),
db.PrimaryKeyConstraint('followed_id', 'follower_id')
)

# solved = db.Table('solved',
# db.Column('solver',db.Integer,db.ForeignKey('user.id')),
# db.Column('solved',db.Integer,db.ForeignKey('challenge.id')),
# db.Column('time',db.DateTime),
# db.PrimaryKeyConstraint('solved', 'solver')
# )

unlocked = db.Table('unlocked',
db.Column('user',db.Integer,db.ForeignKey('user.id')),
db.Column('unlocked',db.Integer,db.ForeignKey('challenge.id')),
db.PrimaryKeyConstraint('user', 'unlocked')
)

class Challenge(db.Model):
    __searchable__ = ['title','text']
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(100),nullable = False)
    text = db.Column(db.String(1000),nullable = False)
    min_lvl = db.Column(db.Integer, default = 0,nullable = False)
    solution = db.Column(db.String(140),default = 'Thanatos')

    def __repr__(self):
        return '<Challenge %r:%r>' % (self.id,self.title)


if enable_search:
    whooshalchemy.whoosh_index(app, Challenge)
