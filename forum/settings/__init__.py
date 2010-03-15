from base import Setting, SettingSet

from django.forms.widgets import Textarea

BASIC_SET = SettingSet('basic', 'Basic Settings', "The basic settings for your application", 1)

APP_TITLE = Setting('APP_TITLE', 'OSQA: Open Source Q&A Forum', BASIC_SET, dict(
label = "Application title",
help_text = """
The title of your application that will show in the browsers title bar
"""))

APP_SHORT_NAME = Setting('APP_SHORT_NAME', 'OSQA', BASIC_SET, dict(
label = "Application short name",
help_text = """
The short name for your application that will show up in many places.
"""))

APP_KEYWORDS = Setting('APP_KEYWORDS', 'OSQA,CNPROG,forum,community', BASIC_SET, dict(
label = "Application keywords",
help_text = """
The meta keywords that will be available through the HTML meta tags.
"""))

APP_DESCRIPTION = Setting('APP_DESCRIPTION', 'Ask and answer questions.', BASIC_SET, dict(
label = "Application description",
help_text = """
The description of your application
""",
widget=Textarea))

APP_INTRO = Setting('APP_INTRO', '<p>Ask and answer questions, make the world better!</p>', BASIC_SET, dict(
label = "Application intro",
help_text = """
The introductory page that is visible in the sidebar for anonymous users.
""",
widget=Textarea))

APP_COPYRIGHT = Setting('APP_COPYRIGHT', 'Copyright OSQA, 2009. Some rights reserved under creative commons license.', BASIC_SET, dict(
label = "Copyright notice",
help_text = """
The copyright notice visible at the footer of your page.
"""))

EXT_KEYS_SET = SettingSet('extkeys', 'External Keys', "Keys for various external providers that your application may optionally use.", 100)

GOOGLE_SITEMAP_CODE = Setting('GOOGLE_SITEMAP_CODE', '', EXT_KEYS_SET, dict(
label = "Google sitemap code",
help_text = """
This is the code you get when you register your site at <a href="https://www.google.com/webmasters/tools/">Google webmaster central</a>.
""",
required=False))

GOOGLE_ANALYTICS_KEY = Setting('GOOGLE_ANALYTICS_KEY', '', EXT_KEYS_SET, dict(
label = "Google analytics key",
help_text = """
Your Google analytics key. You can get one at the <a href="http://www.google.com/analytics/">Google analytics official website</a>
""",
required=False))

MIN_REP_SET = SettingSet('minrep', 'Minimum reputation config', "Configure the minimum reputation required to perform certain actions on your site.", 300)

REP_TO_VOTE_UP = Setting('REP_TO_VOTE_UP', 15, MIN_REP_SET, dict(
label = "Minimum reputation to vote up",
help_text = """
The minimum reputation an user must have to be allowed to vote up.
"""))

REP_TO_VOTE_DOWN = Setting('REP_TO_VOTE_DOWN', 100, MIN_REP_SET, dict(
label = "Minimum reputation to vote down",
help_text = """
The minimum reputation an user must have to be allowed to vote down.
"""))

REP_TO_FLAG = Setting('REP_TO_FLAG', 15, MIN_REP_SET, dict(
label = "Minimum reputation to flag a post",
help_text = """
The minimum reputation an user must have to be allowed to flag a post.
"""))

REP_TO_COMMENT = Setting('REP_TO_COMMENT', 50, MIN_REP_SET, dict(
label = "Minimum reputation to comment",
help_text = """
The minimum reputation an user must have to be allowed to comment a post.
"""))

REP_TO_UPLOAD = Setting('REP_TO_UPLOAD', 60, MIN_REP_SET, dict(
label = "Minimum reputation to upload",
help_text = """
The minimum reputation an user must have to be allowed to upload a file.
"""))

REP_TO_CLOSE_OWN = Setting('REP_TO_CLOSE_OWN', 250, MIN_REP_SET, dict(
label = "Minimum reputation to close own question",
help_text = """
The minimum reputation an user must have to be allowed to close his own question.
"""))

REP_TO_REOPEN_OWN = Setting('REP_TO_REOPEN_OWN', 500, MIN_REP_SET, dict(
label = "Minimum reputation to reopen own question",
help_text = """
The minimum reputation an user must have to be allowed to reopen his own question.
"""))

REP_TO_RETAG = Setting('REP_TO_RETAG', 500, MIN_REP_SET, dict(
label = "Minimum reputation to retag others questions",
help_text = """
The minimum reputation an user must have to be allowed to retag others questions.
"""))

REP_TO_EDIT_WIKI = Setting('REP_TO_EDIT_WIKI', 750, MIN_REP_SET, dict(
label = "Minimum reputation to edit wiki posts",
help_text = """
The minimum reputation an user must have to be allowed to edit community wiki posts.
"""))

REP_TO_EDIT_OTHERS = Setting('REP_TO_EDIT_OTHERS', 2000, MIN_REP_SET, dict(
label = "Minimum reputation to edit others posts",
help_text = """
The minimum reputation an user must have to be allowed to edit others posts.
"""))

REP_TO_CLOSE_OTHERS = Setting('REP_TO_CLOSE_OTHERS', 3000, MIN_REP_SET, dict(
label = "Minimum reputation to close others posts",
help_text = """
The minimum reputation an user must have to be allowed to close others posts.
"""))

REP_TO_LOCK = Setting('REP_TO_LOCK', 4000, MIN_REP_SET, dict(
label = "Minimum reputation to lock posts",
help_text = """
The minimum reputation an user must have to be allowed to lock posts.
"""))

REP_TO_DELLETE_COMMENTS = Setting('REP_TO_DELLETE_COMMENTS', 2000, MIN_REP_SET, dict(
label = "Minimum reputation to delete comments",
help_text = """
The minimum reputation an user must have to be allowed to delete comments.
"""))

REP_TO_VIEW_FLAGS = Setting('REP_TO_VIEW_FLAGS', 2000, MIN_REP_SET, dict(
label = "Minimum reputation to view offensive flags",
help_text = """
The minimum reputation an user must have to view offensive flags.
"""))

REP_TO_DISABLE_NOFOLLOW = Setting('REP_TO_DISABLE_NOFOLLOW', 2000, MIN_REP_SET, dict(
label = "Minimum reputation to disable nofollow",
help_text = """
The minimum reputation an user must have to be allowed to disable the nofollow attribute of a post link.
"""))

REP_GAIN_SET = SettingSet('repgain', 'Reputation gains and losses config', "Configure the reputation points a user may gain or lose upon certain actions.", 200)

INITIAL_REP = Setting('INITIAL_REP', 1, REP_GAIN_SET, dict(
label = "Initial reputation",
help_text = """
The initial reputation an user gets when he first signs in.
"""))

MAX_REP_BY_UPVOTE_DAY = Setting('MAX_REP_BY_UPVOTE_DAY', 200, REP_GAIN_SET, dict(
label = "Max rep by up votes / day",
help_text = """
Maximum reputation a user can gain in one day for being upvoted.
"""))

REP_GAIN_BY_UPVOTED = Setting('REP_GAIN_BY_UPVOTED', 10, REP_GAIN_SET, dict(
label = "Rep gain by upvoted",
help_text = """
Reputation a user gains for having one of his posts up voted.
"""))

REP_LOST_BY_UPVOTE_CANCELED = Setting('REP_LOST_BY_UPVOTE_CANCELED', 10, REP_GAIN_SET, dict(
label = "Rep lost bu upvote canceled",
help_text = """
Reputation a user loses for having one of the upvotes on his posts canceled.
"""))

REP_LOST_BY_DOWNVOTED = Setting('REP_LOST_BY_DOWNVOTED', 2, REP_GAIN_SET, dict(
label = "Rep lost by downvoted",
help_text = """
Reputation a user loses for having one of his posts down voted.
"""))

REP_LOST_BY_DOWNVOTING = Setting('REP_LOST_BY_DOWNVOTING', 1, REP_GAIN_SET, dict(
label = "Rep lost by downvoting",
help_text = """
Reputation a user loses for down voting a post.
"""))

REP_GAIN_BY_DOWNVOTE_CANCELED = Setting('REP_GAIN_BY_DOWNVOTE_CANCELED', 2, REP_GAIN_SET, dict(
label = "Rep gain by downvote canceled",
help_text = """
Reputation a user gains for having one of the downvotes on his posts canceled.
"""))

REP_GAIN_BY_CANCELING_DOWNVOTE = Setting('REP_GAIN_BY_CANCELING_DOWNVOTE', 1, REP_GAIN_SET, dict(
label = "Rep gain by canceling downvote",
help_text = """
Reputation a user gains for canceling a downvote.
"""))

REP_GAIN_BY_ACCEPTED = Setting('REP_GAIN_BY_ACCEPTED', 15, REP_GAIN_SET, dict(
label = "Rep gain by accepted answer",
help_text = """
Reputation a user gains for having one of his answers accepted.
"""))

REP_GAIN_BY_ACCEPTED_CANCELED = Setting('REP_GAIN_BY_ACCEPTED_CANCELED', 15, REP_GAIN_SET, dict(
label = "Rep lost by accepted canceled",
help_text = """
Reputation a user loses for having one of his accepted answers canceled.
"""))

REP_GAIN_BY_ACCEPTING = Setting('REP_GAIN_BY_ACCEPTING', 2, REP_GAIN_SET, dict(
label = "Rep gain by accepting answer",
help_text = """
Reputation a user gains for accepting an answer to one of his questions.
"""))

REP_LOST_BY_CANCELING_ACCEPTED = Setting('REP_LOST_BY_CANCELING_ACCEPTED', 2, REP_GAIN_SET, dict(
label = "Rep lost by canceling accepted",
help_text = """
Reputation a user loses by canceling an accepted answer.
"""))

REP_LOST_BY_FLAGGED = Setting('REP_LOST_BY_FLAGGED', 2, REP_GAIN_SET, dict(
label = "Rep lost by post flagged",
help_text = """
Reputation a user loses by having one of his posts flagged.
"""))

REP_LOST_BY_FLAGGED_3_TIMES = Setting('REP_LOST_BY_FLAGGED_3_TIMES', 30, REP_GAIN_SET, dict(
label = "Rep lost by post flagged 3 times",
help_text = """
Reputation a user loses by having the last revision of one of his posts flagged 3 times.
"""))

REP_LOST_BY_FLAGGED_5_TIMES = Setting('REP_LOST_BY_FLAGGED_5_TIMES', 100, REP_GAIN_SET, dict(
label = "Rep lost by post flagged 5 times",
help_text = """
Reputation a user loses by having the last revision of one of his posts flagged 5 times.
"""))

VOTE_RULES_SET = SettingSet('voting', 'Voting rules', "Configure the voting rules on your site.", 400)

MAX_VOTES_PER_DAY = Setting('MAX_VOTES_PER_DAY', 30, VOTE_RULES_SET, dict(
label = "Maximum votes per day",
help_text = """
The maximum number of votes an user can cast per day.
"""))

START_WARN_VOTES_LEFT = Setting('START_WARN_VOTES_LEFT', 10, VOTE_RULES_SET, dict(
label = "Start warning about votes left",
help_text = """
From how many votes left should an user start to be warned about it.
"""))

MAX_FLAGS_PER_DAY = Setting('MAX_FLAGS_PER_DAY', 5, VOTE_RULES_SET, dict(
label = "Maximum flags per day",
help_text = """
The maximum number of times an can flag a post per day.
"""))

FLAG_COUNT_TO_HIDE_POST = Setting('FLAG_COUNT_TO_HIDE_POST', 3, VOTE_RULES_SET, dict(
label = "Flag count to hide post",
help_text = """
How many times a post needs to be flagged to be hidden from the main page.
"""))

FLAG_COUNT_TO_DELETE_POST = Setting('FLAG_COUNT_TO_DELETE_POST', 5, VOTE_RULES_SET, dict(
label = "Flag count to delete post",
help_text = """
How many times a post needs to be flagged to be deleted.
"""))

DENY_UNVOTE_DAYS = Setting('DENY_UNVOTE_DAYS', 1, VOTE_RULES_SET, dict(
label = "Days to cancel a vote",
help_text = """
How many days an user can cancel a vote after he originaly casted it.
"""))

BADGES_SET = SettingSet('badges', 'Badges config', "Configure badges on your OSQA site.", 500)

from pages import *

__all__ = locals().keys()