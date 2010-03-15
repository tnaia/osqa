"""
Authorisation related functions.

The actions a User is authorised to perform are dependent on their reputation
and superuser status.
"""
import datetime
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _
from django.db import transaction
from models import Repute
from models import Question
from models import Answer
import logging
import settings

def can_moderate_users(user):
    return user.is_superuser

def can_vote_up(user):
    """Determines if a User can vote Questions and Answers up."""
    return user.is_authenticated() and (
        user.reputation >= settings.REP_TO_VOTE_UP or
        user.is_superuser)

def can_flag_offensive(user):
    """Determines if a User can flag Questions and Answers as offensive."""
    return user.is_authenticated() and (
        user.reputation >= settings.REP_TO_FLAG or
        user.is_superuser)

def can_add_comments(user,subject):
    """Determines if a User can add comments to Questions and Answers."""
    if user.is_authenticated():
        if user.id == subject.author.id:
            return True
        if user.reputation >= settings.REP_TO_COMMENT:
            return True
        if user.is_superuser:
            return True
        if isinstance(subject,Answer) and subject.question.author.id == user.id:
            return True
    return False

def can_vote_down(user):
    """Determines if a User can vote Questions and Answers down."""
    return user.is_authenticated() and (
        user.reputation >= settings.REP_TO_VOTE_DOWN or
        user.is_superuser)

def can_retag_questions(user):
    """Determines if a User can retag Questions."""
    return user.is_authenticated() and (
        settings.REP_TO_RETAG <= user.reputation < settings.REP_TO_EDIT_OTHERS or
        user.is_superuser)

def can_edit_post(user, post):
    """Determines if a User can edit the given Question or Answer."""
    return user.is_authenticated() and (
        user.id == post.author_id or
        (post.wiki and user.reputation >= settings.REP_TO_EDIT_WIKI) or
        user.reputation >= settings.REP_TO_EDIT_OTHERS or
        user.is_superuser)

def can_delete_comment(user, comment):
    """Determines if a User can delete the given Comment."""
    return user.is_authenticated() and (
        user.id == comment.user_id or
        user.reputation >= settings.REP_TO_DELETE_COMMENTS or
        user.is_superuser)

def can_view_offensive_flags(user):
    """Determines if a User can view offensive flag counts."""
    return user.is_authenticated() and (
        user.reputation >= settings.REP_TO_VIEW_FLAGS or
        user.is_superuser)

def can_close_question(user, question):
    """Determines if a User can close the given Question."""
    return user.is_authenticated() and (
        (user.id == question.author_id and
         user.reputation >= settings.REP_TO_CLOSE_OWN) or
        user.reputation >= settings.REP_TO_CLOSE_OTHERS or
        user.is_superuser)

def can_lock_posts(user):
    """Determines if a User can lock Questions or Answers."""
    return user.is_authenticated() and (
        user.reputation >= settings.REP_TO_LOCK or
        user.is_superuser)

def can_follow_url(user):
    """Determines if the URL link can be followed by Google search engine."""
    return user.reputation >= settings.REP_TO_DISABLE_NOFOLLOW

def can_accept_answer(user, question, answer):
    return (user.is_authenticated() and
        question.author != answer.author and
        question.author == user) or user.is_superuser

# now only support to reopen own question except superuser
def can_reopen_question(user, question):
    return (user.is_authenticated() and
        user.id == question.author_id and
        user.reputation >= settings.REP_TO_REOPEN_OWN) or user.is_superuser

def can_delete_post(user, post):
    if user.is_superuser:
        return True
    elif user.is_authenticated() and user == post.author:
        if isinstance(post,Answer):
            return True
        elif isinstance(post,Question):
            answers = post.answers.all()
            for answer in answers:
                if user != answer.author and answer.deleted == False:
                    return False
            return True
        else:
            return False
    else:
        return False

def can_view_deleted_post(user, post):
    return user.is_superuser

# user preferences view permissions
def is_user_self(request_user, target_user):
    return (request_user.is_authenticated() and request_user == target_user)
    
def can_view_user_votes(request_user, target_user):
    return (request_user.is_authenticated() and request_user == target_user)

def can_view_user_preferences(request_user, target_user):
    return (request_user.is_authenticated() and request_user == target_user)

def can_view_user_edit(request_user, target_user):
    return (request_user.is_authenticated() and request_user == target_user)

def can_upload_files(request_user):
    return (request_user.is_authenticated() and request_user.reputation >= settings.REP_TO_UPLOAD) or \
           request_user.is_superuser

###########################################
## actions and reputation changes event
###########################################
def calculate_reputation(origin, offset):
    result = int(origin) + int(offset)
    if (result > 0):
        return result
    else:
        return 1

@transaction.commit_on_success
def onFlaggedItem(item, post, user):

    item.save()
    post.offensive_flag_count = post.offensive_flag_count + 1
    post.save()

    post.author.reputation = calculate_reputation(post.author.reputation,
                           -int(settings.REP_LOST_BY_FLAGGED))
    post.author.save()

    question = post
    if post.__class__ == Answer:
        question = post.question

    reputation = Repute(user=post.author,
               negative=-int(settings.REP_LOST_BY_FLAGGED),
               question=question, reputed_at=datetime.datetime.now(),
               reputation_type=-4,
               reputation=post.author.reputation)
    reputation.save()

    #todo: These should be updated to work on same revisions.
    if post.offensive_flag_count == settings.FLAG_COUNT_TO_HIDE_POST :
        post.author.reputation = calculate_reputation(post.author.reputation,
                               -int(settings.REP_LOST_BY_FLAGGED_3_TIMES))
        post.author.save()

        reputation = Repute(user=post.author,
                   negative=-int(settings.REP_LOST_BY_FLAGGED_3_TIMES),
                   question=question,
                   reputed_at=datetime.datetime.now(),
                   reputation_type=-6,
                   reputation=post.author.reputation)
        reputation.save()

    elif post.offensive_flag_count == settings.FLAG_COUNT_TO_DELETE_POST:
        post.author.reputation = calculate_reputation(post.author.reputation,
                               -int(settings.REP_LOST_BY_FLAGGED_5_TIMES))
        post.author.save()

        reputation = Repute(user=post.author,
                   negative=-int(settings.REP_LOST_BY_FLAGGED_5_TIMES),
                   question=question,
                   reputed_at=datetime.datetime.now(),
                   reputation_type=-7,
                   reputation=post.author.reputation)
        reputation.save()

        post.deleted = True
        #post.deleted_at = datetime.datetime.now()
        #post.deleted_by = Admin
        post.save()


@transaction.commit_on_success
def onAnswerAccept(answer, user):
    answer.accepted = True
    answer.accepted_at = datetime.datetime.now()
    answer.question.answer_accepted = True
    answer.save()
    answer.question.save()

    answer.author.reputation = calculate_reputation(answer.author.reputation,
                             int(settings.REP_GAIN_BY_ACCEPTED))
    answer.author.save()
    reputation = Repute(user=answer.author,
               positive=int(settings.REP_GAIN_BY_ACCEPTED),
               question=answer.question,
               reputed_at=datetime.datetime.now(),
               reputation_type=2,
               reputation=answer.author.reputation)
    reputation.save()

    user.reputation = calculate_reputation(user.reputation,
                    int(settings.REP_GAIN_BY_ACCEPTING))
    user.save()
    reputation = Repute(user=user,
               positive=int(settings.REP_GAIN_BY_ACCEPTING),
               question=answer.question,
               reputed_at=datetime.datetime.now(),
               reputation_type=3,
               reputation=user.reputation)
    reputation.save()

@transaction.commit_on_success
def onAnswerAcceptCanceled(answer, user):
    answer.accepted = False
    answer.accepted_at = None
    answer.question.answer_accepted = False
    answer.save()
    answer.question.save()

    answer.author.reputation = calculate_reputation(answer.author.reputation,
                             -int(settings.REP_GAIN_BY_ACCEPTED_CANCELED))
    answer.author.save()
    reputation = Repute(user=answer.author,
               negative=-int(settings.REP_GAIN_BY_ACCEPTED_CANCELED),
               question=answer.question,
               reputed_at=datetime.datetime.now(),
               reputation_type=-2,
               reputation=answer.author.reputation)
    reputation.save()

    user.reputation = calculate_reputation(user.reputation,
                    -int(settings.REP_LOST_BY_CANCELING_ACCEPTED))
    user.save()
    reputation = Repute(user=user,
               negative=-int(settings.REP_LOST_BY_CANCELING_ACCEPTED),
               question=answer.question,
               reputed_at=datetime.datetime.now(),
               reputation_type=-1,
               reputation=user.reputation)
    reputation.save()

@transaction.commit_on_success
def onUpVoted(vote, post, user):
    vote.save()

    post.increment_vote_up_count()
    post.score = int(post.score) + 1
    post.save()

    if not post.wiki:
        author = post.author
        if Repute.objects.get_reputation_by_upvoted_today(author) <  int(settings.MAX_REP_BY_UPVOTE_DAY):
            author.reputation = calculate_reputation(author.reputation,
                              int(settings.REP_GAIN_BY_UPVOTED))
            author.save()

            question = post
            if post.__class__ == Answer:
                question = post.question

            reputation = Repute(user=author,
                       positive=int(settings.REP_GAIN_BY_UPVOTED),
                       question=question,
                       reputed_at=datetime.datetime.now(),
                       reputation_type=1,
                       reputation=author.reputation)
            reputation.save()

@transaction.commit_on_success
def onUpVotedCanceled(vote, post, user):
    vote.delete()

    post.decrement_vote_up_count()
    if post.vote_up_count < 0:
        post.vote_up_count  = 0
    post.score = int(post.score) - 1
    post.save()

    if not post.wiki:
        author = post.author
        author.reputation = calculate_reputation(author.reputation,
                          -int(settings.REP_LOST_BY_UPVOTE_CANCELED))
        author.save()

        question = post
        if post.__class__ == Answer:
            question = post.question

        reputation = Repute(user=author,
                   negative=-int(settings.REP_LOST_BY_UPVOTE_CANCELED),
                   question=question,
                   reputed_at=datetime.datetime.now(),
                   reputation_type=-8,
                   reputation=author.reputation)
        reputation.save()

@transaction.commit_on_success
def onDownVoted(vote, post, user):
    vote.save()

    post.vote_down_count = int(post.vote_down_count) + 1
    post.score = int(post.score) - 1
    post.save()

    if not post.wiki:
        author = post.author
        author.reputation = calculate_reputation(author.reputation,
                          -int(settings.REP_LOST_BY_DOWNVOTED))
        author.save()

        question = post
        if post.__class__ == Answer:
            question = post.question

        reputation = Repute(user=author,
                   negative=-int(settings.REP_LOST_BY_DOWNVOTED),
                   question=question,
                   reputed_at=datetime.datetime.now(),
                   reputation_type=-3,
                   reputation=author.reputation)
        reputation.save()

        user.reputation = calculate_reputation(user.reputation,
                        -int(settings.REP_LOST_BY_DOWNVOTING))
        user.save()

        reputation = Repute(user=user,
                   negative=-int(settings.REP_LOST_BY_DOWNVOTING),
                   question=question,
                   reputed_at=datetime.datetime.now(),
                   reputation_type=-5,
                   reputation=user.reputation)
        reputation.save()

@transaction.commit_on_success
def onDownVotedCanceled(vote, post, user):
    vote.delete()

    post.vote_down_count = int(post.vote_down_count) - 1
    if post.vote_down_count < 0:
        post.vote_down_count  = 0
    post.score = post.score + 1
    post.save()

    if not post.wiki:
        author = post.author
        author.reputation = calculate_reputation(author.reputation,
                          int(settings.REP_GAIN_BY_DOWNVOTE_CANCELED))
        author.save()

        question = post
        if post.__class__ == Answer:
            question = post.question

        reputation = Repute(user=author,
                   positive=int(settings.REP_GAIN_BY_DOWNVOTE_CANCELED),
                   question=question,
                   reputed_at=datetime.datetime.now(),
                   reputation_type=4,
                   reputation=author.reputation)
        reputation.save()

        user.reputation = calculate_reputation(user.reputation,
                        int(settings.REP_GAIN_BY_CANCELING_DOWNVOTE))
        user.save()

        reputation = Repute(user=user,
                   positive=int(settings.REP_GAIN_BY_CANCELING_DOWNVOTE),
                   question=question,
                   reputed_at=datetime.datetime.now(),
                   reputation_type=5,
                   reputation=user.reputation)
        reputation.save()

def onDeleteCanceled(post, user):
    post.deleted = False
    post.deleted_by = None 
    post.deleted_at = None 
    post.save()
    logging.debug('now restoring something')
    if isinstance(post,Answer):
        logging.debug('updated answer count on undelete, have %d' % post.question.answer_count)
        Question.objects.update_answer_count(post.question)
    elif isinstance(post,Question):
        for tag in list(post.tags.all()):
            if tag.used_count == 1 and tag.deleted:
                tag.deleted = False
                tag.deleted_by = None
                tag.deleted_at = None 
                tag.save()

def onDeleted(post, user):
    post.deleted = True
    post.deleted_by = user
    post.deleted_at = datetime.datetime.now()
    post.save()

    if isinstance(post, Question):
        for tag in list(post.tags.all()):
            if tag.used_count == 1:
                tag.deleted = True
                tag.deleted_by = user
                tag.deleted_at = datetime.datetime.now()
            else:
                tag.used_count = tag.used_count - 1 
            tag.save()

        answers = post.answers.all()
        if user == post.author:
            if len(answers) > 0:
                msg = _('Your question and all of it\'s answers have been deleted')
            else:
                msg = _('Your question has been deleted')
        else:
            if len(answers) > 0:
                msg = _('The question and all of it\'s answers have been deleted')
            else:
                msg = _('The question has been deleted')
        user.message_set.create(message=msg)
        logging.debug('posted a message %s' % msg)
        for answer in answers:
            onDeleted(answer, user)
    elif isinstance(post, Answer):
        Question.objects.update_answer_count(post.question)
        logging.debug('updated answer count to %d' % post.question.answer_count)
