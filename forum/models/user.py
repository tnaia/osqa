from base import *
from forum import const
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User as DjangoUser
from hashlib import md5
import string
from random import Random

from django.utils.translation import ugettext as _
import django.dispatch


QUESTIONS_PER_PAGE_CHOICES = (
   (10, u'10'),
   (30, u'30'),
   (50, u'50'),
)

class User(DjangoUser):
    is_approved = models.BooleanField(default=False)
    email_isvalid = models.BooleanField(default=False)
    email_key = models.CharField(max_length=32, null=True)
    reputation = models.PositiveIntegerField(default=1)
    gravatar = models.CharField(max_length=32)

    gold = models.SmallIntegerField(default=0)
    silver = models.SmallIntegerField(default=0)
    bronze = models.SmallIntegerField(default=0)

    questions_per_page = models.SmallIntegerField(choices=QUESTIONS_PER_PAGE_CHOICES, default=10)
    last_seen = models.DateTimeField(default=datetime.datetime.now)
    real_name = models.CharField(max_length=100, blank=True)
    website = models.URLField(max_length=200, blank=True)
    location = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    about = models.TextField(blank=True)

    hide_ignored_questions = models.BooleanField(default=False)
    tag_filter_setting = models.CharField(max_length=16, choices=TAG_EMAIL_FILTER_CHOICES, default='ignored')

    @classmethod
    def user_is_username_taken(cls,username):
        try:
            cls.objects.get(username=username)
            return True
        except cls.MultipleObjectsReturned:
            return True
        except cls.DoesNotExist:
            return False

    def user_get_absolute_url(self):
        return "/users/%d/%s/" % (self.id, (self.username))

    def get_messages(self):
        messages = []
        for m in self.message_set.all():
            messages.append(m.message)
        return messages

    def delete_messages(self):
        self.message_set.all().delete()

    def get_profile_url(self):
        """Returns the URL for this User's profile."""
        return "/users/%d/%s" % (self.id, slugify(self.username))

    def get_profile_link(self):
        profile_link = u'<a href="%s">%s</a>' % (self.get_profile_url(),self.username)
        logging.debug('in get profile link %s' % profile_link)
        return mark_safe(profile_link)

    class Meta:
        app_label = 'forum'

class Activity(models.Model):
    """
    We keep some history data for user activities
    """
    user = models.ForeignKey(User)
    activity_type = models.SmallIntegerField(choices=TYPE_ACTIVITY)
    active_at = models.DateTimeField(default=datetime.datetime.now)
    content_type   = models.ForeignKey(ContentType)
    object_id      = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    is_auditted    = models.BooleanField(default=False)

    class Meta:
        app_label = 'forum'
        db_table = u'activity'

    def __unicode__(self):
        return u'[%s] was active at %s' % (self.user.username, self.active_at)

    def save(self):
        super(Activity, self).save()
        if self._is_new:
            activity_record.send(sender=self.activity_type, instance=self)

    @property
    def question(self):
        if self.activity_type == const.TYPE_ACTIVITY_ASK_QUESTION:
            return self.content_object
        elif self.activity_type in (const.TYPE_ACTIVITY_ANSWER,
                const.TYPE_ACTIVITY_MARK_ANSWER, const.TYPE_ACTIVITY_UPDATE_QUESTION):
            return self.content_object.question
        elif self.activity_type == const.TYPE_ACTIVITY_COMMENT_QUESTION:
            return self.content_object.content_object
        elif self.activity_type == const.TYPE_ACTIVITY_COMMENT_ANSWER:
            return self.content_object.content_object.question
        elif self.activity_type == const.TYPE_ACTIVITY_UPDATE_ANSWER:
            return self.content_object.content_object.answer.question
        else:
            raise NotImplementedError()

    @property
    def type_as_string(self):
        if self.activity_type == const.TYPE_ACTIVITY_ASK_QUESTION:
            return _("asked")
        elif self.activity_type  == const.TYPE_ACTIVITY_ANSWER:
            return _("answered")
        elif self.activity_type  == const.TYPE_ACTIVITY_MARK_ANSWER:
            return _("marked an answer")
        elif self.activity_type  == const.TYPE_ACTIVITY_UPDATE_QUESTION:
            return _("edited")
        elif self.activity_type == const.TYPE_ACTIVITY_COMMENT_QUESTION:
            return _("commented")
        elif self.activity_type == const.TYPE_ACTIVITY_COMMENT_ANSWER:
            return _("commented an answer")
        elif self.activity_type == const.TYPE_ACTIVITY_UPDATE_ANSWER:
            return _("edited an answer")
        else:
            raise NotImplementedError()


activity_record = django.dispatch.Signal(providing_args=['instance'])

class SubscriptionSettings(models.Model):
    user = models.OneToOneField(User, related_name='subscription_settings')

    enable_notifications = models.BooleanField(default=True)

    #notify if
    member_joins = models.CharField(max_length=1, default='n', choices=const.NOTIFICATION_CHOICES)
    new_question = models.CharField(max_length=1, default='d', choices=const.NOTIFICATION_CHOICES)
    new_question_watched_tags = models.CharField(max_length=1, default='i', choices=const.NOTIFICATION_CHOICES)
    subscribed_questions = models.CharField(max_length=1, default='i', choices=const.NOTIFICATION_CHOICES)
    
    #auto_subscribe_to
    all_questions = models.BooleanField(default=False)
    all_questions_watched_tags = models.BooleanField(default=False)
    questions_asked = models.BooleanField(default=True)
    questions_answered = models.BooleanField(default=True)
    questions_commented = models.BooleanField(default=False)
    questions_viewed = models.BooleanField(default=False)

    #notify activity on subscribed
    notify_answers = models.BooleanField(default=True)
    notify_reply_to_comments = models.BooleanField(default=True)
    notify_comments_own_post = models.BooleanField(default=True)
    notify_comments = models.BooleanField(default=False)
    notify_accepted = models.BooleanField(default=False)

    class Meta:
        app_label = 'forum'

from forum.utils.time import one_day_from_now

class ValidationHashManager(models.Manager):
    def _generate_md5_hash(self, user, type, hash_data, seed):
        return md5("%s%s%s%s" % (seed, "".join(map(str, hash_data)), user.id, type)).hexdigest()

    def create_new(self, user, type, hash_data=[], expiration=None):
        seed = ''.join(Random().sample(string.letters+string.digits, 12))
        hash = self._generate_md5_hash(user, type, hash_data, seed)

        obj = ValidationHash(hash_code=hash, seed=seed, user=user, type=type)

        if expiration is not None:
            obj.expiration = expiration

        try:
            obj.save()
        except:
            return None
            
        return obj

    def validate(self, hash, user, type, hash_data=[]):
        try:
            obj = self.get(hash_code=hash)
        except:
            return False

        if obj.type != type:
            return False

        if obj.user != user:
            return False

        valid = (obj.hash_code == self._generate_md5_hash(obj.user, type, hash_data, obj.seed))

        if valid:
            if obj.expiration < datetime.datetime.now():
                obj.delete()
                return False
            else:
                obj.delete()
                return True

        return False

class ValidationHash(models.Model):
    hash_code = models.CharField(max_length=255,unique=True)
    seed = models.CharField(max_length=12)
    expiration = models.DateTimeField(default=one_day_from_now)
    type = models.CharField(max_length=12)
    user = models.ForeignKey(User)

    objects = ValidationHashManager()

    class Meta:
        unique_together = ('user', 'type')
        app_label = 'forum'

    def __str__(self):
        return self.hash_code

class AuthKeyUserAssociation(models.Model):
    key = models.CharField(max_length=255,null=False,unique=True)
    provider = models.CharField(max_length=64)
    user = models.ForeignKey(User, related_name="auth_keys")
    added_at = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        app_label = 'forum'
