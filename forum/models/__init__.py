from question import Question ,QuestionRevision, AnonymousQuestion, FavoriteQuestion, QuestionSubscription
from answer import Answer, AnonymousAnswer, AnswerRevision
from tag import Tag, MarkedTag
from meta import Vote, Comment, FlaggedItem
from user import User, Activity, ValidationHash, AuthKeyUserAssociation, SubscriptionSettings
from repute import Badge, Award, Repute
from utils import KeyValue
import re

from base import *

try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], [r"^forum\.models\.utils\.\w+"])
except:
    pass

# custom signal
tags_updated = django.dispatch.Signal(providing_args=["question"])
edit_question_or_answer = django.dispatch.Signal(providing_args=["instance", "modified_by"])
delete_post_or_answer = django.dispatch.Signal(providing_args=["instance", "deleted_by"])
mark_offensive = django.dispatch.Signal(providing_args=["instance", "mark_by"])
user_updated = django.dispatch.Signal(providing_args=["instance", "updated_by"])
user_logged_in = django.dispatch.Signal(providing_args=["session"])

def calculate_gravatar_hash(instance, **kwargs):
    """Calculates a User's gravatar hash from their email address."""
    if kwargs.get('raw', False):
        return
    instance.gravatar = hashlib.md5(instance.email).hexdigest()

def record_ask_event(instance, created, **kwargs):
    if created:
        activity = Activity(user=instance.author, active_at=instance.added_at, content_object=instance, activity_type=TYPE_ACTIVITY_ASK_QUESTION)
        activity.save()

#todo: translate this
record_answer_event_re = re.compile("You have received (a|\d+) .*new response.*")
def record_answer_event(instance, created, **kwargs):
    if created:
        q_author = instance.question.author
        found_match = False
        #print 'going through %d messages' % q_author.message_set.all().count()
        for m in q_author.message_set.all():
            #print m.message
            match = record_answer_event_re.search(m.message)
            if match:
                found_match = True
                try:
                    cnt = int(match.group(1))
                except:
                    cnt = 1
                m.message = u"You have received %d <a href=\"%s?sort=responses\">new responses</a>."\
                            % (cnt+1, q_author.get_profile_url())
                #print 'updated message'
                #print m.message
                m.save()
                break
        if not found_match:
            msg = u"You have received a <a href=\"%s?sort=responses\">new response</a>."\
                    % q_author.get_profile_url()
            #print 'new message'
            #print msg
            q_author.message_set.create(message=msg)

        activity = Activity(user=instance.author, \
                            active_at=instance.added_at,\
                            content_object=instance, \
                            activity_type=TYPE_ACTIVITY_ANSWER)
        activity.save()

def record_comment_event(instance, created, **kwargs):
    if created:
        from django.contrib.contenttypes.models import ContentType
        question_type = ContentType.objects.get_for_model(Question)
        question_type_id = question_type.id
        if (instance.content_type_id == question_type_id):
            type = TYPE_ACTIVITY_COMMENT_QUESTION
        else:
            type = TYPE_ACTIVITY_COMMENT_ANSWER
        activity = Activity(user=instance.user, active_at=instance.added_at, content_object=instance, activity_type=type)
        activity.save()

def record_revision_question_event(instance, created, **kwargs):
    if created and instance.revision <> 1:
        activity = Activity(user=instance.author, active_at=instance.revised_at, content_object=instance, activity_type=TYPE_ACTIVITY_UPDATE_QUESTION)
        activity.save()

def record_revision_answer_event(instance, created, **kwargs):
    if created and instance.revision <> 1:
        activity = Activity(user=instance.author, active_at=instance.revised_at, content_object=instance, activity_type=TYPE_ACTIVITY_UPDATE_ANSWER)
        activity.save()

def record_award_event(instance, created, **kwargs):
    """
    After we awarded a badge to user, we need to record this activity and notify user.
    We also recaculate awarded_count of this badge and user information.
    """
    if created:
        activity = Activity(user=instance.user, active_at=instance.awarded_at, content_object=instance,
            activity_type=TYPE_ACTIVITY_PRIZE)
        activity.save()

        instance.badge.awarded_count += 1
        instance.badge.save()

        if instance.badge.type == Badge.GOLD:
            instance.user.gold += 1
        if instance.badge.type == Badge.SILVER:
            instance.user.silver += 1
        if instance.badge.type == Badge.BRONZE:
            instance.user.bronze += 1
        instance.user.save()

def notify_award_message(instance, created, **kwargs):
    """
    Notify users when they have been awarded badges by using Django message.
    """
    if created:
        user = instance.user

        msg = (u"Congratulations, you have received a badge '%s'. " \
                + u"Check out <a href=\"%s\">your profile</a>.") \
                % (instance.badge.name, user.get_profile_url())

        user.message_set.create(message=msg)

def record_answer_accepted(instance, created, **kwargs):
    """
    when answer is accepted, we record this for question author - who accepted it.
    """
    if not created and instance.accepted:
        activity = Activity(user=instance.question.author, active_at=datetime.datetime.now(), \
            content_object=instance, activity_type=TYPE_ACTIVITY_MARK_ANSWER)
        activity.save()

def update_last_seen(instance, created, **kwargs):
    """
    when user has activities, we update 'last_seen' time stamp for him
    """
    user = instance.user
    user.last_seen = datetime.datetime.now()
    user.save()

def record_vote(instance, created, **kwargs):
    """
    when user have voted
    """
    if created:
        if instance.vote == 1:
            vote_type = TYPE_ACTIVITY_VOTE_UP
        else:
            vote_type = TYPE_ACTIVITY_VOTE_DOWN

        activity = Activity(user=instance.user, active_at=instance.voted_at, content_object=instance, activity_type=vote_type)
        activity.save()

def record_cancel_vote(instance, **kwargs):
    """
    when user canceled vote, the vote will be deleted.
    """
    activity = Activity(user=instance.user, active_at=datetime.datetime.now(), content_object=instance, activity_type=TYPE_ACTIVITY_CANCEL_VOTE)
    activity.save()

def record_delete_question(instance, delete_by, **kwargs):
    """
    when user deleted the question
    """
    if instance.__class__ is Question:
        activity_type = TYPE_ACTIVITY_DELETE_QUESTION
    else:
        activity_type = TYPE_ACTIVITY_DELETE_ANSWER

    activity = Activity(user=delete_by, active_at=datetime.datetime.now(), content_object=instance, activity_type=activity_type)
    activity.save()

def record_mark_offensive(instance, mark_by, **kwargs):
    activity = Activity(user=mark_by, active_at=datetime.datetime.now(), content_object=instance, activity_type=TYPE_ACTIVITY_MARK_OFFENSIVE)
    activity.save()

def record_update_tags(question, **kwargs):
    """
    when user updated tags of the question
    """
    activity = Activity(user=question.author, active_at=datetime.datetime.now(), content_object=question, activity_type=TYPE_ACTIVITY_UPDATE_TAGS)
    activity.save()

def record_favorite_question(instance, created, **kwargs):
    """
    when user add the question in him favorite questions list.
    """
    if created:
        activity = Activity(user=instance.user, active_at=datetime.datetime.now(), content_object=instance, activity_type=TYPE_ACTIVITY_FAVORITE)
        activity.save()

def record_user_full_updated(instance, **kwargs):
    activity = Activity(user=instance, active_at=datetime.datetime.now(), content_object=instance, activity_type=TYPE_ACTIVITY_USER_FULL_UPDATED)
    activity.save()

def post_stored_anonymous_content(sender,user,session_key,signal,*args,**kwargs):
    aq_list = AnonymousQuestion.objects.filter(session_key = session_key)
    aa_list = AnonymousAnswer.objects.filter(session_key = session_key)
    import settings
    if settings.EMAIL_VALIDATION == 'on':#add user to the record
        for aq in aq_list:
            aq.author = user
            aq.save()
        for aa in aa_list:
            aa.author = user
            aa.save()
        #maybe add pending posts message?
    else: #just publish the questions
        for aq in aq_list:
            aq.publish(user)
        for aa in aa_list:
            aa.publish(user)

def is_new(sender, instance, **kwargs):
    try:
        instance._is_new = not bool(instance.id)
    except:
        pass

#signal for User modle save changes
pre_save.connect(is_new)
pre_save.connect(calculate_gravatar_hash, sender=User)
post_save.connect(record_ask_event, sender=Question)
post_save.connect(record_answer_event, sender=Answer)
post_save.connect(record_comment_event, sender=Comment)
post_save.connect(record_revision_question_event, sender=QuestionRevision)
post_save.connect(record_revision_answer_event, sender=AnswerRevision)
post_save.connect(record_award_event, sender=Award)
post_save.connect(notify_award_message, sender=Award)
post_save.connect(record_answer_accepted, sender=Answer)
post_save.connect(update_last_seen, sender=Activity)
post_save.connect(record_vote, sender=Vote)
post_delete.connect(record_cancel_vote, sender=Vote)
delete_post_or_answer.connect(record_delete_question, sender=Question)
delete_post_or_answer.connect(record_delete_question, sender=Answer)
mark_offensive.connect(record_mark_offensive, sender=Question)
mark_offensive.connect(record_mark_offensive, sender=Answer)
tags_updated.connect(record_update_tags, sender=Question)
post_save.connect(record_favorite_question, sender=FavoriteQuestion)
user_updated.connect(record_user_full_updated, sender=User)
user_logged_in.connect(post_stored_anonymous_content)

__all__ = [
        'Question',
        'QuestionRevision',
        'FavoriteQuestion',
        'AnonymousQuestion',
        'QuestionSubscription',

        'Answer',
        'AnswerRevision',
        'AnonymousAnswer',

        'Tag',
        'Comment',
        'Vote',
        'FlaggedItem',
        'MarkedTag',

        'Badge',
        'Award',
        'Repute',

        'Activity',
        'ValidationHash',
        'AuthKeyUserAssociation',
        'SubscriptionSettings',
        'KeyValue',

        'User',
        'tags_updated',
        'edit_question_or_answer', 
        'delete_post_or_answer',
        'mark_offensive',
        'user_updated',
        'user_logged_in',
        ]


from forum.modules import get_modules_script_classes

for k, v in get_modules_script_classes('models', models.Model).items():
    if not k in __all__:
        __all__.append(k)
        exec "%s = v" % k
