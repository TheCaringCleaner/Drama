from sqlalchemy.orm import deferred, aliased
from secrets import token_hex
import pyotp
from files.helpers.discord import remove_user
from files.helpers.images import *
from files.helpers.const import *
from .alts import Alt
from .submission import SaveRelationship
from .comment import Notification
from .award import AwardRelationship
from .subscriptions import *
from .userblock import *
from .badges import *
from .clients import *
from files.__main__ import Base, cache
from files.helpers.security import *
import random
from os import environ

site = environ.get("DOMAIN").strip()
site_name = environ.get("SITE_NAME").strip()
defaulttheme = environ.get("DEFAULT_THEME", "midnight").strip()
defaultcolor = environ.get("DEFAULT_COLOR", "fff").strip()
defaulttimefilter = environ.get("DEFAULT_TIME_FILTER", "all").strip()
cardview = bool(int(environ.get("CARD_VIEW", 1)))

class User(Base):
	__tablename__ = "users"

	if "pcmemes.net" in site:
		quadrant = Column(String)
		basedcount = Column(Integer, default=0)
		pills = deferred(Column(String, default=""))

	id = Column(Integer, primary_key=True)
	username = Column(String)
	namecolor = Column(String, default=defaultcolor)
	background = Column(String)
	customtitle = Column(String)
	customtitleplain = deferred(Column(String))
	titlecolor = Column(String, default=defaultcolor)
	theme = Column(String, default=defaulttheme)
	themecolor = Column(String, default=defaultcolor)
	cardview = Column(Boolean, default=cardview)
	song = Column(String)
	highres = Column(String)
	profileurl = Column(String)
	bannerurl = Column(String)
	patron = Column(Integer, default=0)
	verified = Column(String)
	verifiedcolor = Column(String)
	marseyawarded = Column(Integer)
	longpost = Column(Integer)
	email = deferred(Column(String))
	css = deferred(Column(String))
	profilecss = deferred(Column(String))
	passhash = deferred(Column(String))
	post_count = Column(Integer, default=0)
	comment_count = Column(Integer, default=0)
	received_award_count = Column(Integer, default=0)
	created_utc = Column(Integer, default=0)
	suicide_utc = Column(Integer, default=0)
	rent_utc = Column(Integer, default=0)
	steal_utc = Column(Integer, default=0)
	fail_utc = Column(Integer, default=0)
	fail2_utc = Column(Integer, default=0)
	admin_level = Column(Integer, default=0)
	coins_spent = Column(Integer, default=0)
	agendaposter = Column(Boolean, default=False)
	agendaposter_expires_utc = Column(Integer, default=0)
	changelogsub = Column(Boolean, default=False)
	is_activated = Column(Boolean, default=False)
	shadowbanned = Column(String)
	over_18 = Column(Boolean, default=False)
	hidevotedon = Column(Boolean, default=False)
	highlightcomments = Column(Boolean, default=True)
	slurreplacer = Column(Boolean, default=True)
	flairchanged = Column(Integer)
	newtab = Column(Boolean, default=False)
	newtabexternal = Column(Boolean, default=True)
	oldreddit = Column(Boolean, default=True)
	nitter = Column(Boolean)
	mute = Column(Boolean)
	unmutable = Column(Boolean)
	eye = Column(Boolean)
	alt = Column(Boolean)
	frontsize = Column(Integer, default=25)
	controversial = Column(Boolean, default=False)
	bio = deferred(Column(String))
	bio_html = Column(String)
	sig = deferred(Column(String))
	sig_html = Column(String)
	fp = Column(String)
	sigs_disabled = Column(Boolean)
	friends = deferred(Column(String))
	friends_html = deferred(Column(String))
	enemies = deferred(Column(String))
	enemies_html = deferred(Column(String))
	is_banned = Column(Integer, default=0)
	unban_utc = Column(Integer, default=0)
	ban_reason = deferred(Column(String))
	club_banned = Column(Boolean, default=False)
	club_allowed = Column(Boolean, default=False)
	login_nonce = Column(Integer, default=0)
	reserved = deferred(Column(String))
	coins = Column(Integer, default=0)
	truecoins = Column(Integer, default=0)
	procoins = Column(Integer, default=0)
	mfa_secret = deferred(Column(String))
	is_private = Column(Boolean, default=False)
	stored_subscriber_count = Column(Integer, default=0)
	defaultsortingcomments = Column(String, default="top")
	defaultsorting = Column(String, default="hot")
	defaulttime = Column(String, default=defaulttimefilter)
	is_nofollow = Column(Boolean, default=False)
	custom_filter_list = Column(String)
	discord_id = Column(String)
	ban_evade = Column(Integer, default=0)
	original_username = deferred(Column(String))
	referred_by = Column(Integer, ForeignKey("users.id"))

	badges = relationship("Badge", viewonly=True)
	subscriptions = relationship("Subscription", viewonly=True)
	following = relationship("Follow", primaryjoin="Follow.user_id==User.id", viewonly=True)
	followers = relationship("Follow", primaryjoin="Follow.target_id==User.id", viewonly=True)
	viewers = relationship("ViewerRelationship", primaryjoin="User.id == ViewerRelationship.user_id", viewonly=True)
	blocking = relationship("UserBlock", lazy="dynamic", primaryjoin="User.id==UserBlock.user_id", viewonly=True)
	blocked = relationship("UserBlock", lazy="dynamic", primaryjoin="User.id==UserBlock.target_id", viewonly=True)
	authorizations = relationship("ClientAuth", viewonly=True)
	awards = relationship("AwardRelationship", primaryjoin="User.id==AwardRelationship.user_id", viewonly=True)
	referrals = relationship("User", viewonly=True)

	def __init__(self, **kwargs):

		if "password" in kwargs:
			kwargs["passhash"] = self.hash_password(kwargs["password"])
			kwargs.pop("password")

		kwargs["created_utc"] = int(time.time())

		super().__init__(**kwargs)


	@property
	@lazy
	def csslazy(self):
		return self.css

	@property
	@lazy
	def notifications(self):
		return g.db.query(Notification).filter_by(user_id=self.id)

	@property
	@lazy
	def created_date(self):

		return time.strftime("%d %b %Y", time.gmtime(self.created_utc))

	@property
	@lazy
	def user_awards(self):

		return_value = list(AWARDS2.values())

		user_awards = g.db.query(AwardRelationship).filter_by(user_id=self.id)

		for val in return_value: val['owned'] = user_awards.filter_by(kind=val['kind'], submission_id=None, comment_id=None).count()

		return return_value

	@property
	def referral_count(self):
		return len(self.referrals)

	def has_block(self, target):

		return g.db.query(UserBlock).filter_by(
			user_id=self.id, target_id=target.id).first()

	@property
	@lazy
	def paid_dues(self):
		return self.admin_level > 1 or self.club_allowed or (self.truecoins > int(environ.get("DUES").strip()) and not self.club_banned)

	def any_block_exists(self, other):

		return g.db.query(UserBlock).filter(
			or_(and_(UserBlock.user_id == self.id, UserBlock.target_id == other.id), and_(
				UserBlock.user_id == other.id, UserBlock.target_id == self.id))).first()

	def validate_2fa(self, token):

		x = pyotp.TOTP(self.mfa_secret)
		return x.verify(token, valid_window=1)

	@property
	@lazy
	def age(self):
		return int(time.time()) - self.created_utc

	@property
	@lazy
	def alts_unique(self):
		alts = []
		for u in self.alts:
			if u not in alts: alts.append(u)
		return alts

	@property
	@lazy
	def strid(self):
		return str(self.id)

	@cache.memoize(timeout=86400)
	def userpagelisting(self, v=None, page=1, sort="new", t="all"):

		if self.shadowbanned and not (v and (v.admin_level > 1 or v.id == self.id)):
			return []

		posts = g.db.query(Submission.id).filter_by(author_id=self.id, is_pinned=False)

		if not (v and (v.admin_level > 1 or v.id == self.id)):
			posts = posts.filter_by(deleted_utc=0, is_banned=False, private=False)

		now = int(time.time())
		if t == 'hour':
			cutoff = now - 3600
		elif t == 'day':
			cutoff = now - 86400
		elif t == 'week':
			cutoff = now - 604800
		elif t == 'month':
			cutoff = now - 2592000
		elif t == 'year':
			cutoff = now - 31536000
		else:
			cutoff = 0
		posts = posts.filter(Submission.created_utc >= cutoff)

		if sort == "new":
			posts = posts.order_by(Submission.created_utc.desc())
		elif sort == "old":
			posts = posts.order_by(Submission.created_utc.asc())
		elif sort == "controversial":
			posts = posts.order_by(-1 * Submission.upvotes * Submission.downvotes * Submission.downvotes)
		elif sort == "top":
			posts = posts.order_by(Submission.downvotes - Submission.upvotes)
		elif sort == "bottom":
			posts = posts.order_by(Submission.upvotes - Submission.downvotes)
		elif sort == "comments":
			posts = posts.order_by(Submission.comment_count.desc())

		posts = posts.offset(25 * (page - 1)).limit(26).all()

		return [x[0] for x in posts]

	@property
	@lazy
	def bio_html_eager(self):
		return self.bio_html.replace('data-src', 'src').replace('src="/assets/images/loading.webp"', '')

	@property
	@lazy
	def fullname(self):
		return f"t1_{self.id}"

	@property
	@lazy
	def banned_by(self):
		if not self.is_suspended: return None
		return g.db.query(User).filter_by(id=self.is_banned).first()

	def has_badge(self, badgedef_id):
		return g.db.query(Badge).filter_by(user_id=self.id, badge_id=badgedef_id).first()

	def hash_password(self, password):
		return generate_password_hash(
			password, method='pbkdf2:sha512', salt_length=8)

	def verifyPass(self, password):
		return check_password_hash(self.passhash, password)

	@property
	@lazy
	def formkey(self):

		if "session_id" not in session:
			session["session_id"] = token_hex(16)

		msg = f"{session['session_id']}+{self.id}+{self.login_nonce}"

		return generate_hash(msg)

	def validate_formkey(self, formkey):

		return validate_hash(f"{session['session_id']}+{self.id}+{self.login_nonce}", formkey)

	@property
	@lazy
	def url(self):
		return f"/@{self.username}"

	def __repr__(self):
		return f"<User(username={self.username})>"

	@property
	@lazy
	def unban_string(self):
		if self.unban_utc == 0:
			return "permanently banned"

		wait = self.unban_utc - int(time.time())

		if wait < 60:
			text = f"{wait}s"
		else:
			days = wait//(24*60*60)
			wait -= days*24*60*60

			hours = wait//(60*60)
			wait -= hours*60*60

			mins = wait//60

			text = f"{days}d {hours:02d}h {mins:02d}m"

		return f"Unban in {text}"


	@property
	@lazy
	def received_awards(self):

		awards = {}

		posts_idlist = [x[0] for x in g.db.query(Submission.id).filter_by(author_id=self.id).all()]
		comments_idlist = [x[0] for x in g.db.query(Comment.id).filter_by(author_id=self.id).all()]

		post_awards = g.db.query(AwardRelationship).filter(AwardRelationship.submission_id.in_(posts_idlist)).all()
		comment_awards = g.db.query(AwardRelationship).filter(AwardRelationship.comment_id.in_(comments_idlist)).all()

		total_awards = post_awards + comment_awards

		for a in total_awards:
			if a.kind in awards:
				awards[a.kind]['count'] += 1
			else:
				awards[a.kind] = a.type
				awards[a.kind]['count'] = 1

		return sorted(list(awards.values()), key=lambda x: x['kind'], reverse=True)

	@property
	@lazy
	def notifications_count(self):
		return g.db.query(Notification.id).join(Comment).filter(Notification.user_id == self.id, Notification.read == False, Comment.is_banned == False, Comment.deleted_utc == 0).count()

	@property
	@lazy
	def post_notifications_count(self):
		return g.db.query(Notification.id).join(Comment).filter(Notification.user_id == self.id, Notification.read == False, Comment.author_id == AUTOJANNY_ID).count()


	@property
	@lazy
	def alts(self):

		subq = g.db.query(Alt).filter(
			or_(
				Alt.user1 == self.id,
				Alt.user2 == self.id
			)
		).subquery()

		data = g.db.query(
			User,
			aliased(Alt, alias=subq)
		).join(
			subq,
			or_(
				subq.c.user1 == User.id,
				subq.c.user2 == User.id
			)
		).filter(
			User.id != self.id
		).order_by(User.username.asc()).all()

		data = [x for x in data]
		output = []
		for x in data:
			user = x[0]
			user._is_manual = x[1].is_manual
			output.append(user)

		return output

	def has_follower(self, user):

		return g.db.query(Follow).filter_by(target_id=self.id, user_id=user.id).first()

	@property
	@lazy
	def banner_url(self):
		if self.bannerurl: return self.bannerurl
		else: return f"http://{site}/assets/images/{site_name}/preview.webp?v=2"

	@property
	@lazy
	def profile_url(self):
		if self.profileurl: return self.profileurl
		elif "rama" in site: return f"http://{site}/assets/images/defaultpictures/{random.randint(1, 150)}.webp?v=1"
		else: return f"http://{site}/assets/images/default-profile-pic.webp"

	@property
	@lazy
	def json_raw(self):
		data = {'username': self.username,
				'url': self.url,
				'is_banned': bool(self.is_banned),
				'created_utc': self.created_utc,
				'id': self.id,
				'is_private': self.is_private,
				'profile_url': self.profile_url,
				'bannerurl': self.bannerurl,
				'bio': self.bio,
				'bio_html': self.bio_html,
				'flair': self.customtitle
				}

		return data

	@property
	@lazy
	def json_core(self):

		now = int(time.time())
		if self.is_banned and (not self.unban_utc or now < self.unban_utc):
			return {'username': self.username,
					'url': self.url,
					'is_banned': True,
					'is_permanent_ban': not bool(self.unban_utc),
					'ban_reason': self.ban_reason,
					'id': self.id
					}
		return self.json_raw

	@property
	@lazy
	def json(self):
		data = self.json_core

		data["badges"] = [x.json_core for x in self.badges]
		data['coins'] = int(self.coins)
		data['post_count'] = self.post_count
		data['comment_count'] = self.comment_count

		return data

	def ban(self, admin=None, reason=None, days=0):

		if days > 0:
			ban_time = int(time.time()) + (days * 86400)
			self.unban_utc = ban_time
		else:
			self.bannerurl = None
			self.profileurl = None
			if self.discord_id: remove_user(self)

		self.is_banned = admin.id if admin else AUTOJANNY_ID
		if reason: self.ban_reason = reason

		g.db.add(self)


	@property
	@lazy
	def is_suspended(self):
		if self.unban_utc and self.unban_utc < time.time():
			self.is_banned = 0
			self.unban_utc = 0
			self.ban_evade = 0
			g.db.add(self)
			g.db.commit()
		return (self.is_banned and (not self.unban_utc or self.unban_utc > time.time()))


	@property
	@lazy
	def applications(self):
		return g.db.query(OauthApp).filter_by(author_id=self.id).order_by(OauthApp.id.asc()).all()

	@lazy
	def subscribed_idlist(self, page=1):
		posts = g.db.query(Subscription.submission_id).filter_by(user_id=self.id).all()
		return [x[0] for x in posts]

	@lazy
	def saved_idlist(self, page=1):

		posts = g.db.query(Submission.id).filter_by(is_banned=False, deleted_utc=0)

		saved = [x[0] for x in g.db.query(SaveRelationship.submission_id).filter(SaveRelationship.user_id == self.id).all()]
		posts = posts.filter(Submission.id.in_(saved))

		if self.admin_level == 0:
			blocking = [x[0] for x in g.db.query(
				UserBlock.target_id).filter_by(
				user_id=self.id).all()]
			blocked = [x[0] for x in g.db.query(
				UserBlock.user_id).filter_by(
				target_id=self.id).all()]

			posts = posts.filter(
				Submission.author_id.notin_(blocking),
				Submission.author_id.notin_(blocked)
			)

		posts = posts.order_by(Submission.created_utc.desc())

		return [x[0] for x in posts.offset(25 * (page - 1)).limit(26).all()]

	@lazy
	def saved_comment_idlist(self):

		try: saved = [x[0] for x in g.db.query(SaveRelationship.comment_id).filter(SaveRelationship.user_id == self.id).all()]
		except: return []
		comments = g.db.query(Comment.id).filter(Comment.id.in_(saved))

		if self.admin_level == 0:
			blocking = [x[0] for x in g.db.query(
				UserBlock.target_id).filter_by(
				user_id=self.id).all()]
			blocked = [x[0] for x in g.db.query(
				UserBlock.user_id).filter_by(
				target_id=self.id).all()]

			comments = comments.filter(
				Comment.author_id.notin_(blocking),
				Comment.author_id.notin_(blocked)
			)

		return [x[0] for x in comments.order_by(Comment.created_utc.desc()).all()]

	@property
	@lazy
	def filter_words(self):
		l = [i.strip() for i in self.custom_filter_list.split('\n')] if self.custom_filter_list else []
		l = [i for i in l if i]
		return l


class ViewerRelationship(Base):

	__tablename__ = "viewers"

	id = Column(Integer, Sequence('viewers_id_seq'), primary_key=True)
	user_id = Column(Integer, ForeignKey('users.id'))
	viewer_id = Column(Integer, ForeignKey('users.id'))
	last_view_utc = Column(Integer)

	viewer = relationship("User", primaryjoin="ViewerRelationship.viewer_id == User.id", viewonly=True)

	def __init__(self, **kwargs):

		if 'last_view_utc' not in kwargs:
			kwargs['last_view_utc'] = int(time.time())

		super().__init__(**kwargs)

	@property
	@lazy
	def last_view_since(self):

		return int(time.time()) - self.last_view_utc

	@property
	@lazy
	def last_view_string(self):

		age = self.last_view_since

		if age < 60:
			return "just now"
		elif age < 3600:
			minutes = int(age / 60)
			return f"{minutes}m ago"
		elif age < 86400:
			hours = int(age / 3600)
			return f"{hours}hr ago"
		elif age < 2678400:
			days = int(age / 86400)
			return f"{days}d ago"

		now = time.gmtime()
		ctd = time.gmtime(self.created_utc)

		months = now.tm_mon - ctd.tm_mon + 12 * (now.tm_year - ctd.tm_year)
		if now.tm_mday < ctd.tm_mday:
			months -= 1

		if months < 12:
			return f"{months}mo ago"
		else:
			years = int(months / 12)
			return f"{years}yr ago"