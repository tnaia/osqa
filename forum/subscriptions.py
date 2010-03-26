import os
import re
import datetime
from forum.models import User, Question, Comment, QuestionSubscription, SubscriptionSettings
from forum.models.user import activity_record
from forum.utils.mail import send_email
from forum.views.readers import question_view
from django.utils.translation import ugettext as _
from django.conf import settings
from django.db.models import Q, F
from django.db.models.signals import post_save
from django.contrib.contenttypes.models import ContentType
import const

def create_subscription_if_not_exists(question, user):
    try:
        subscription = QuestionSubscription.objects.get(question=question, user=user)
    except:
        subscription = QuestionSubscription(question=question, user=user)
        subscription.save()

def apply_default_filters(queryset, excluded_id):
    return queryset.values('email', 'username').exclude(id=excluded_id)

def create_recipients_dict(usr_list):
    return [(s['username'], s['email'], {'username': s['username']}) for s in usr_list]

def question_posted(sender, instance, **kwargs):
    question = instance.content_object

    subscribers = User.objects.values('email', 'username').filter(
            Q(subscription_settings__enable_notifications=True, subscription_settings__new_question='i') |
            (Q(subscription_settings__new_question_watched_tags='i') &
              Q(marked_tags__name__in=question.tagnames.split(' ')) &
              Q(tag_selections__reason='good'))
    ).exclude(id=question.author.id)

    recipients = create_recipients_dict(subscribers)

    send_email(settings.EMAIL_SUBJECT_PREFIX + _("New question on %s") % settings.APP_SHORT_NAME,
               recipients, "notifications/newquestion.html", {
        'question': question,
    })

    if question.author.subscription_settings.questions_asked:
        subscription = QuestionSubscription(question=question, user=question.author)
        subscription.save()

    new_subscribers = User.objects.filter(
            Q(subscription_settings__all_questions=True) |
            Q(subscription_settings__all_questions_watched_tags=True,
                    marked_tags__name__in=question.tagnames.split(' '),
                    tag_selections__reason='good'))

    for user in new_subscribers:
        create_subscription_if_not_exists(question, user)

activity_record.connect(question_posted, sender=const.TYPE_ACTIVITY_ASK_QUESTION, weak=False)


def answer_posted(sender, instance, **kwargs):
    answer = instance.content_object
    question = answer.question

    subscribers = question.subscribers.values('email', 'username').filter(
            subscription_settings__enable_notifications=True,
            subscription_settings__notify_answers=True,
            subscription_settings__subscribed_questions='i'
    ).exclude(id=answer.author.id)
    recipients = create_recipients_dict(subscribers)

    send_email(settings.EMAIL_SUBJECT_PREFIX + _("New answer to '%s'") % question.title,
               recipients, "notifications/newanswer.html", {
        'question': question,
        'answer': answer
    })

    if answer.author.subscription_settings.questions_answered:
        create_subscription_if_not_exists(question, answer.author)

activity_record.connect(answer_posted, sender=const.TYPE_ACTIVITY_ANSWER, weak=False)


def comment_posted(sender, instance, **kwargs):
    comment = instance.content_object
    post = comment.content_object

    if post.__class__ == Question:
        question = post
    else:
        question = post.question

    subscribers = question.subscribers.values('email', 'username')

    q_filter = Q(subscription_settings__notify_comments=True) | Q(subscription_settings__notify_comments_own_post=True, id=post.author.id)

    inreply = re.search('@\w+', comment.comment)
    if inreply is not None:
        q_filter = q_filter | Q(subscription_settings__notify_reply_to_comments=True,
                                username__istartswith=inreply.group(0)[1:],
                                comments__object_id=post.id,
                                comments__content_type=ContentType.objects.get_for_model(post.__class__)
                                )

    subscribers = subscribers.filter(
            q_filter, subscription_settings__subscribed_questions='i', subscription_settings__enable_notifications=True 
    ).exclude(id=comment.user.id)

    recipients = create_recipients_dict(subscribers)

    send_email(settings.EMAIL_SUBJECT_PREFIX + _("New comment on %s") % question.title,
               recipients, "notifications/newcomment.html", {
                'comment': comment,
                'post': post,
                'question': question,
    })

    if comment.user.subscription_settings.questions_commented:
        create_subscription_if_not_exists(question, comment.user)

activity_record.connect(comment_posted, sender=const.TYPE_ACTIVITY_COMMENT_QUESTION, weak=False)
activity_record.connect(comment_posted, sender=const.TYPE_ACTIVITY_COMMENT_ANSWER, weak=False)


def answer_accepted(sender, instance, **kwargs):
    answer = instance.content_object
    question = answer.question

    subscribers = question.subscribers.values('email', 'username').filter(
            subscription_settings__enable_notifications=True,
            subscription_settings__notify_accepted=True,
            subscription_settings__subscribed_questions='i'
    ).exclude(id=question.author.id)
    recipients = create_recipients_dict(subscribers)

    send_email(settings.EMAIL_SUBJECT_PREFIX + _("An answer to '%s' was accepted") % question.title,
               recipients, "notifications/answeraccepted.html", {
        'question': question,
        'answer': answer
    })

activity_record.connect(answer_accepted, sender=const.TYPE_ACTIVITY_MARK_ANSWER, weak=False)


def member_joined(sender, instance, **kwargs):
    if not instance._is_new:
        return
        
    subscribers = User.objects.values('email', 'username').filter(
            subscription_settings__enable_notifications=True,
            subscription_settings__member_joins='i'
    ).exclude(id=instance.id)

    recipients = create_recipients_dict(subscribers)

    send_email(settings.EMAIL_SUBJECT_PREFIX + _("%s is a new member on %s") % (instance.username, settings.APP_SHORT_NAME),
               recipients, "notifications/newmember.html", {
        'newmember': instance,
    })

    sub_settings = SubscriptionSettings(user=instance)
    sub_settings.save()

post_save.connect(member_joined, sender=User, weak=False)

def question_viewed(sender, user, **kwargs):
    try:
        subscription = QuestionSubscription.objects.get(question=sender, user=user)
        subscription.last_view = datetime.datetime.now()
        subscription.save()
    except:
        if user.subscription_settings.questions_viewed:
            subscription = QuestionSubscription(question=sender, user=user)
            subscription.save()

question_view.connect(question_viewed)
