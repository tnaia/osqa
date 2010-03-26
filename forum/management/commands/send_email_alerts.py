<<<<<<< HEAD
from datetime import datetime, timedelta
from django.core.management.base import NoArgsCommand
from django.utils.translation import ugettext as _
from django.template import loader, Context, Template
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from forum.models import KeyValue, Activity, User, QuestionSubscription
from forum.utils.mail import send_msg_list
from forum import const

class QuestionRecord:
    def __init__(self, question):
        self.question = question
        self.records = []

    def log_activity(self, activity):
        self.records.append(activity)

    def get_activity_since(self, since):
        activity = [r for r in self.records if r.active_at > since]
        answers = [a for a in activity if a.activity_type == const.TYPE_ACTIVITY_ANSWER]
        comments = [a for a in activity if a.activity_type in (const.TYPE_ACTIVITY_COMMENT_QUESTION, const.TYPE_ACTIVITY_COMMENT_ANSWER)]

        accepted = [a for a in activity if a.activity_type == const.TYPE_ACTIVITY_MARK_ANSWER]

        if len(accepted):
            accepted = accepted[-1:][0]
        else:
            accepted = None

        return {
            'answers': answers,
            'comments': comments,
            'accepted': accepted,
        }


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        digest_control = self.get_digest_control()

        self.send_digest('daily', 'd', digest_control.value['LAST_DAILY'])
        digest_control.value['LAST_DAILY'] = datetime.now()

        if digest_control.value['LAST_WEEKLY'] + timedelta(days=7) <= datetime.now():
            self.send_digest('weekly', 'w', digest_control.value['LAST_WEEKLY'])
            digest_control.value['LAST_WEEKLY'] = datetime.now()

        digest_control.save()
            

    def send_digest(self, name, char_in_db, control_date):
        new_questions, question_records = self.prepare_activity(control_date)
        new_users = User.objects.filter(date_joined__gt=control_date)

        digest_template = loader.get_template("notifications/digest.html")
        digest_subject = settings.EMAIL_SUBJECT_PREFIX + _('Daily digest')

        users = User.objects.filter(subscription_settings__enable_notifications=True)

        msgs = []

        for u in users:
            context = {
                'user': u,
                'digest_type': name,
            }

            if u.subscription_settings.member_joins == char_in_db:
                context['new_users'] = new_users
            else:
                context['new_users'] = False

            if u.subscription_settings.subscribed_questions == char_in_db:
                activity_in_subscriptions = []

                for id, r in question_records.items():
                    try:
                        subscription = QuestionSubscription.objects.get(question=r.question, user=u)

                        record = r.get_activity_since(subscription.last_view)

                        if not u.subscription_settings.notify_answers:
                            del record['answers']

                        if not u.subscription_settings.notify_comments:
                            if u.subscription_settings.notify_comments_own_post:
                                record.comments = [a for a in record.comments if a.content_object.content_object.author == u]
                                record['own_comments_only'] = True
                            else:
                                del record['comments']

                        if not u.subscription_settings.notify_accepted:
                            del record['accepted']

                        if record.get('answers', False) or record.get('comments', False) or record.get('accepted', False):
                            activity_in_subscriptions.append({'question': r.question, 'activity': record})
                    except:
                        pass

                context['activity_in_subscriptions'] = activity_in_subscriptions
            else:
                context['activity_in_subscriptions'] = False


            if u.subscription_settings.new_question == char_in_db:
                context['new_questions'] = new_questions
                context['watched_tags_only'] = False
            elif u.subscription_settings.new_question_watched_tags == char_in_db:
                context['new_questions'] = [q for q in new_questions if
                                            q.tags.filter(id__in=u.marked_tags.filter(user_selections__reason='good')).count() > 0]
                context['watched_tags_only'] = True
            else:
                context['new_questions'] = False

            if context['new_users'] or context['activity_in_subscriptions'] or context['new_questions']:
                message_body = digest_template.render(Context(context))

                msg = EmailMultiAlternatives(digest_subject, message_body, settings.DEFAULT_FROM_EMAIL, [u.email])
                msg.attach_alternative(message_body, "text/html")

                msgs.append(msg)
        
        send_msg_list(msgs)


    def get_digest_control(self):
        try:
            digest_control = KeyValue.objects.get(key='DIGEST_CONTROL')
        except:
            digest_control = KeyValue(key='DIGEST_CONTROL', value={
                'LAST_DAILY': datetime.now() - timedelta(days=1),
                'LAST_WEEKLY': datetime.now() - timedelta(days=1),
            })

        return digest_control

    def prepare_activity(self, since):
        all_activity = Activity.objects.filter(active_at__gt=since, activity_type__in=(
            const.TYPE_ACTIVITY_ASK_QUESTION, const.TYPE_ACTIVITY_ANSWER,
            const.TYPE_ACTIVITY_COMMENT_QUESTION, const.TYPE_ACTIVITY_COMMENT_ANSWER,
            const.TYPE_ACTIVITY_MARK_ANSWER
        )).order_by('active_at')

        question_records = {}
        new_questions = []


        for activity in all_activity:
            try:
                question = self.get_question_for_activity(activity)

                if not question.id in question_records:
                    question_records[question.id] = QuestionRecord(question)

                question_records[question.id].log_activity(activity)

                if activity.activity_type == const.TYPE_ACTIVITY_ASK_QUESTION:
                    new_questions.append(question)
            except:
                pass

        return new_questions, question_records

    def get_question_for_activity(self, activity):
        if activity.activity_type == const.TYPE_ACTIVITY_ASK_QUESTION:
            question = activity.content_object
        elif activity.activity_type == const.TYPE_ACTIVITY_ANSWER:
            question = activity.content_object.question
        elif activity.activity_type == const.TYPE_ACTIVITY_COMMENT_QUESTION:
            question = activity.content_object.content_object
        elif activity.activity_type == const.TYPE_ACTIVITY_COMMENT_ANSWER:
            question = activity.content_object.content_object.question
        elif activity.activity_type == const.TYPE_ACTIVITY_MARK_ANSWER:
            question = activity.content_object.question
        else:
            raise Exception

        return question
=======
from django.core.management.base import NoArgsCommand
from django.db import connection
from django.db.models import Q, F
from forum.models import *
from django.core.mail import EmailMessage
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
import datetime
from forum import const
from forum import settings
from django.conf import settings as django_settings
import logging
from forum.utils.odict import OrderedDict
from django.contrib.contenttypes.models import ContentType

def extend_question_list(src, dst, limit=False):
    """src is a query set with questions
       or None
       dst - is an ordered dictionary
    """
    if limit and len(dst.keys()) >= settings.MAX_ALERTS_PER_EMAIL:
        return
    if src is None:#is not QuerySet
        return #will not do anything if subscription of this type is not used
    cutoff_time = src.cutoff_time
    for q in src:
        if q in dst:
            #the latest cutoff time wins for a given question
            #if the question falls into several subscription groups
            if cutoff_time > dst[q]['cutoff_time']:
                dst[q]['cutoff_time'] = cutoff_time
        else:
            #initialise a questions metadata dictionary to use for email reporting
            dst[q] = {'cutoff_time':cutoff_time}

class Command(NoArgsCommand):
    def handle_noargs(self,**options):
        try:
            try:
                self.send_email_alerts()
            except Exception, e:
                print e
        finally:
            connection.close()

    def get_updated_questions_for_user(self,user):

        #these are placeholders for separate query sets per question group
        #there are four groups - one for each EmailFeedSetting.feed_type
        #and each group has subtypes A and B
        #that's because of the strange thing commented below
        #see note on Q and F objects marked with todo tag
        q_sel_A = None
        q_sel_B = None

        q_ask_A = None
        q_ask_B = None

        q_ans_A = None
        q_ans_B = None

        q_all_A = None
        q_all_B = None

        now = datetime.datetime.now()
        #Q_set1 - base questionquery set for this user
        Q_set1 = Question.objects.exclude(
                                last_activity_by=user
                            ).exclude(
                                last_activity_at__lt=user.date_joined#exclude old stuff
                            ).exclude(
                                deleted=True
                            ).exclude(
                                closed=True
                            ).order_by('-last_activity_at')
        #todo: for some reason filter on did not work as expected ~Q(viewed__who=user) | 
        #      Q(viewed__who=user,viewed__when__lt=F('last_activity_at'))
        #returns way more questions than you might think it should
        #so because of that I've created separate query sets Q_set2 and Q_set3
        #plus two separate queries run faster!

        #questions that are not seen by the user
        Q_set2 = Q_set1.filter(~Q(viewed__who=user))
        #questions seen before the last modification
        Q_set3 = Q_set1.filter(Q(viewed__who=user,viewed__when__lt=F('last_activity_at')))

        #todo may shortcirquit here is len(user_feeds) == 0
        user_feeds = EmailFeedSetting.objects.filter(subscriber=user).exclude(frequency='n')
        if len(user_feeds) == 0:
            return {};#short cirquit
        for feed in user_feeds:
            #each group of updates has it's own cutoff time
            #to be saved as a new parameter for each query set
            #won't send email for a given question if it has been done
            #after the cutoff_time
            cutoff_time = now - EmailFeedSetting.DELTA_TABLE[feed.frequency]
            if feed.reported_at == None or feed.reported_at <= cutoff_time:
                Q_set_A = Q_set2#.exclude(last_activity_at__gt=cutoff_time)#report these excluded later
                Q_set_B = Q_set3#.exclude(last_activity_at__gt=cutoff_time)
                feed.reported_at = now
                feed.save()#may not actually report anything, depending on filters below
                if feed.feed_type == 'q_sel':
                    q_sel_A = Q_set_A.filter(followed_by=user)
                    q_sel_A.cutoff_time = cutoff_time #store cutoff time per query set
                    q_sel_B = Q_set_B.filter(followed_by=user)
                    q_sel_B.cutoff_time = cutoff_time #store cutoff time per query set
                elif feed.feed_type == 'q_ask':
                    q_ask_A = Q_set_A.filter(author=user)
                    q_ask_A.cutoff_time = cutoff_time
                    q_ask_B = Q_set_B.filter(author=user)
                    q_ask_B.cutoff_time = cutoff_time
                elif feed.feed_type == 'q_ans':
                    q_ans_A = Q_set_A.filter(answers__author=user)[:settings.MAX_ALERTS_PER_EMAIL]
                    q_ans_A.cutoff_time = cutoff_time
                    q_ans_B = Q_set_B.filter(answers__author=user)[:settings.MAX_ALERTS_PER_EMAIL]
                    q_ans_B.cutoff_time = cutoff_time
                elif feed.feed_type == 'q_all':
                    if user.tag_filter_setting == 'ignored':
                        ignored_tags = Tag.objects.filter(user_selections__reason='bad', \
                                                            user_selections__user=user)
                        q_all_A = Q_set_A.exclude( tags__in=ignored_tags )[:settings.MAX_ALERTS_PER_EMAIL]
                        q_all_B = Q_set_B.exclude( tags__in=ignored_tags )[:settings.MAX_ALERTS_PER_EMAIL]
                    else:
                        selected_tags = Tag.objects.filter(user_selections__reason='good', \
                                                            user_selections__user=user)
                        q_all_A = Q_set_A.filter( tags__in=selected_tags )
                        q_all_B = Q_set_B.filter( tags__in=selected_tags )
                    q_all_A.cutoff_time = cutoff_time
                    q_all_B.cutoff_time = cutoff_time
        #build list in this order
        q_list = OrderedDict()

        extend_question_list(q_sel_A, q_list)
        extend_question_list(q_sel_B, q_list)

        if user.tag_filter_setting == 'interesting':
            extend_question_list(q_all_A, q_list)
            extend_question_list(q_all_B, q_list)

        extend_question_list(q_ask_A, q_list, limit=True)
        extend_question_list(q_ask_B, q_list, limit=True)

        extend_question_list(q_ans_A, q_list, limit=True)
        extend_question_list(q_ans_B, q_list, limit=True)

        if user.tag_filter_setting == 'ignored':
            extend_question_list(q_all_A, q_list, limit=True)
            extend_question_list(q_all_B, q_list, limit=True)

        ctype = ContentType.objects.get_for_model(Question)
        EMAIL_UPDATE_ACTIVITY = const.TYPE_ACTIVITY_QUESTION_EMAIL_UPDATE_SENT
        for q, meta_data in q_list.items():
            #this loop edits meta_data for each question
            #so that user will receive counts on new edits new answers, etc
            #maybe not so important actually??

            #keeps email activity per question per user
            try:
                update_info = Activity.objects.get(
                                                    user=user,
                                                    content_type=ctype,
                                                    object_id=q.id,
                                                    activity_type=EMAIL_UPDATE_ACTIVITY
                                                    )
                emailed_at = update_info.active_at
            except Activity.DoesNotExist:
                update_info = Activity(user=user, content_object=q, activity_type=EMAIL_UPDATE_ACTIVITY)
                emailed_at = datetime.datetime(1970,1,1)#long time ago
            except Activity.MultipleObjectsReturned:
                raise Exception('server error - multiple question email activities found per user-question pair')

            cutoff_time = meta_data['cutoff_time']#cutoff time for the question

            #wait some more time before emailing about this question
            if emailed_at > cutoff_time:
                #here we are maybe losing opportunity to record the finding
                #of yet unseen version of a question
                meta_data['skip'] = True
                continue

            #collect info on all sorts of news that happened after
            #the most recent emailing to the user about this question
            q_rev = QuestionRevision.objects.filter(question=q,\
                                                    revised_at__gt=emailed_at)
            q_rev = q_rev.exclude(author=user)

            #now update all sorts of metadata per question
            meta_data['q_rev'] = len(q_rev)
            if len(q_rev) > 0 and q.added_at == q_rev[0].revised_at:
                meta_data['q_rev'] = 0
                meta_data['new_q'] = True
            else:
                meta_data['new_q'] = False
                
            new_ans = Answer.objects.filter(question=q,\
                                            added_at__gt=emailed_at)
            new_ans = new_ans.exclude(author=user)
            meta_data['new_ans'] = len(new_ans)
            ans_rev = AnswerRevision.objects.filter(answer__question=q,\
                                            revised_at__gt=emailed_at)
            ans_rev = ans_rev.exclude(author=user)
            meta_data['ans_rev'] = len(ans_rev)

            if len(q_rev)+len(new_ans)+len(ans_rev) == 0:
                meta_data['skip'] = True
            else:
                meta_data['skip'] = False
                update_info.active_at = now
                update_info.save() #save question email update activity 
        #q_list is actually a ordered dictionary
        #print 'user %s gets %d' % (user.username, len(q_list.keys()))
        #todo: sort question list by update time
        return q_list 

    def __action_count(self,string,number,output):
        if number > 0:
            output.append(_(string) % {'num':number})

    def send_email_alerts(self):
        #does not change the database, only sends the email
        #todo: move this to template
        for user in User.objects.all():
            #todo: q_list is a dictionary, not a list
            q_list = self.get_updated_questions_for_user(user)
            if len(q_list.keys()) == 0:
                continue
            num_q = 0
            num_moot = 0
            for meta_data in q_list.values():
                if meta_data['skip']:
                    num_moot = True
                else:
                    num_q += 1
            if num_q > 0:
                url_prefix = django_settings.APP_URL
                subject = _('email update message subject')
                print 'have %d updated questions for %s' % (num_q, user.username)
                text = ungettext('%(name)s, this is an update message header for a question', 
                            '%(name)s, this is an update message header for %(num)d questions',num_q) \
                                % {'num':num_q, 'name':user.username}

                text += '<ul>'
                items_added = 0
                items_unreported = 0
                for q, meta_data in q_list.items():
                    act_list = []
                    if meta_data['skip']:
                        continue
                    if items_added >= settings.MAX_ALERTS_PER_EMAIL:
                        items_unreported = num_q - items_added #may be inaccurate actually, but it's ok
                        
                    else:
                        items_added += 1
                        if meta_data['new_q']:
                            act_list.append(_('new question'))
                        self.__action_count('%(num)d rev', meta_data['q_rev'],act_list)
                        self.__action_count('%(num)d ans', meta_data['new_ans'],act_list)
                        self.__action_count('%(num)d ans rev',meta_data['ans_rev'],act_list)
                        act_token = ', '.join(act_list)
                        text += '<li><a href="%s?sort=latest">%s</a> <font color="#777777">(%s)</font></li>' \
                                    % (url_prefix + q.get_absolute_url(), q.title, act_token)
                text += '</ul>'
                text += '<p></p>'
                #if len(q_list.keys()) >= settings.MAX_ALERTS_PER_EMAIL:
                #    text += _('There may be more questions updated since '
                #                'you have logged in last time as this list is '
                #                'abridged for your convinience. Please visit '
                #                'the forum and see what\'s new!<br>'
                #              )

                text += _(
                            'Please visit the forum and see what\'s new! '
                            'Could you spread the word about it - '
                            'can somebody you know help answering those questions or '
                            'benefit from posting one?'
                        )

                feeds = EmailFeedSetting.objects.filter(
                                                        subscriber=user,
                                                    )
                feed_freq = [feed.frequency for feed in feeds]
                text += '<p></p>'
                if 'd' in feed_freq:
                    text += _('Your most frequent subscription setting is \'daily\' '
                               'on selected questions. If you are receiving more than one '
                               'email per day'
                               'please tell about this issue to the forum administrator.'
                               )
                elif 'w' in feed_freq:
                    text += _('Your most frequent subscription setting is \'weekly\' '
                               'if you are receiving this email more than once a week '
                               'please report this issue to the forum administrator.'
                               )
                text += ' '
                text += _(
                            'There is a chance that you may be receiving links seen '
                            'before - due to a technicality that will eventually go away. '
                        )
                #    text += '</p>'
                #if num_moot > 0:
                #    text += '<p></p>'
                #    text += ungettext('There is also one question which was recently '\
                #                +'updated but you might not have seen its latest version.',
                #            'There are also %(num)d more questions which were recently updated '\
                #            +'but you might not have seen their latest version.',num_moot) \
                #                % {'num':num_moot,}
                #    text += _('Perhaps you could look up previously sent forum reminders in your mailbox.')
                #    text += '</p>'

                link = url_prefix + user.get_profile_url() + '?sort=email_subscriptions'
                text += _('go to %(link)s to change frequency of email updates or %(email)s administrator') \
                                % {'link':link, 'email':django_settings.ADMINS[0][1]}
                msg = EmailMessage(subject, text, django_settings.DEFAULT_FROM_EMAIL, [user.email])
                msg.content_subtype = 'html'
                msg.send()
                #uncomment lines below to get copies of emails sent to others
                #todo: maybe some debug setting would be appropriate here
                #msg2 = EmailMessage(subject, text, settings.DEFAULT_FROM_EMAIL, ['your@email.com'])
                #msg2.content_subtype = 'html'
                #msg2.send()
>>>>>>> 27341b885f4e0f988f02c95e8f2e5325e263b324
