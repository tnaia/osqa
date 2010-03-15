from datetime import timedelta

from django.db.models.signals import post_save
from django.utils.translation import ugettext as _

from forum.badges.base import PostCountableAbstractBadge, ActivityAbstractBadge, FirstActivityAbstractBadge, \
        ActivityCountAbstractBadge, CountableAbstractBadge, AbstractBadge
from forum.models import Question, Answer, Activity, Tag
from forum.models.user import activity_record
from forum.models.utils import countable_update
from forum.models.tag import tags_update_use_count
from forum import const

import settings

class PopularQuestionBadge(PostCountableAbstractBadge):
    def __init__(self):
        super(PopularQuestionBadge, self).__init__(Question, 'view_count', settings.POPULAR_QUESTION_VIEWS)

class NotableQuestionBadge(PostCountableAbstractBadge):
    def __init__(self):
        super(NotableQuestionBadge, self).__init__(Question, 'view_count', settings.NOTABLE_QUESTION_VIEWS)

class FamousQuestionBadge(PostCountableAbstractBadge):
    def __init__(self):
        super(FamousQuestionBadge, self).__init__(Question, 'view_count', settings.FAMOUS_QUESTION_VIEWS)


class NiceAnswerBadge(PostCountableAbstractBadge):
    def __init__(self):
        super(NiceAnswerBadge, self).__init__(Answer, 'vote_up_count', settings.NICE_ANSWER_VOTES_UP)

class NiceQuestionBadge(PostCountableAbstractBadge):
    def __init__(self):
        super(NiceQuestionBadge, self).__init__(Question, 'vote_up_count', settings.NICE_QUESTION_VOTES_UP)

class GoodAnswerBadge(PostCountableAbstractBadge):
    def __init__(self):
        super(GoodAnswerBadge, self).__init__(Answer, 'vote_up_count', settings.GOOD_ANSWER_VOTES_UP)

class GoodQuestionBadge(PostCountableAbstractBadge):
    def __init__(self):
        super(GoodQuestionBadge, self).__init__(Question, 'vote_up_count', settings.GOOD_QUESTION_VOTES_UP)

class GreatAnswerBadge(PostCountableAbstractBadge):
    def __init__(self):
        super(GreatAnswerBadge, self).__init__(Answer, 'vote_up_count', settings.GREAT_ANSWER_VOTES_UP)

class GreatQuestionBadge(PostCountableAbstractBadge):
    def __init__(self):
        super(GreatQuestionBadge, self).__init__(Question, 'vote_up_count', settings.GREAT_QUESTION_VOTES_UP)


class FavoriteQuestionBadge(PostCountableAbstractBadge):
    def __init__(self):
        super(FavoriteQuestionBadge, self).__init__(Question, 'favourite_count', settings.FAVORITE_QUESTION_FAVS)

class StellarQuestionBadge(PostCountableAbstractBadge):
    def __init__(self):
        super(StellarQuestionBadge, self).__init__(Question, 'favourite_count', settings.STELLAR_QUESTION_FAVS)


class DisciplinedBadge(ActivityAbstractBadge):
    def __init__(self):
        def handler(instance):
            if instance.user.id == instance.content_object.author.id and instance.content_object.score >= settings.DISCIPLINED_MIN_SCORE:
                self.award_badge(instance.user, instance)

        super(DisciplinedBadge, self).__init__(const.TYPE_ACTIVITY_DELETE_QUESTION, handler)

class PeerPressureBadge(ActivityAbstractBadge):
    def __init__(self):
        def handler(instance):
            if instance.user.id == instance.content_object.author.id and instance.content_object.score <= settings.PEER_PRESSURE_MAX_SCORE:
                self.award_badge(instance.user, instance)

        super(PeerPressureBadge, self).__init__(const.TYPE_ACTIVITY_DELETE_QUESTION, handler)


class CitizenPatrolBadge(FirstActivityAbstractBadge):
    def __init__(self):
        super(CitizenPatrolBadge, self).__init__(const.TYPE_ACTIVITY_MARK_OFFENSIVE)

class CriticBadge(FirstActivityAbstractBadge):
    def __init__(self):
        super(CriticBadge, self).__init__(const.TYPE_ACTIVITY_VOTE_DOWN)

class OrganizerBadge(FirstActivityAbstractBadge):
    def __init__(self):
        super(OrganizerBadge, self).__init__(const.TYPE_ACTIVITY_UPDATE_TAGS)

class SupporterBadge(FirstActivityAbstractBadge):
    def __init__(self):
        super(SupporterBadge, self).__init__(const.TYPE_ACTIVITY_VOTE_UP)

class EditorBadge(FirstActivityAbstractBadge):
    def __init__(self):
        super(EditorBadge, self).__init__((const.TYPE_ACTIVITY_UPDATE_ANSWER, const.TYPE_ACTIVITY_UPDATE_QUESTION))

class ScholarBadge(FirstActivityAbstractBadge):
    def __init__(self):
        super(ScholarBadge, self).__init__(const.TYPE_ACTIVITY_MARK_ANSWER)

class AutobiographerBadge(FirstActivityAbstractBadge):
    def __init__(self):
        super(AutobiographerBadge, self).__init__(const.TYPE_ACTIVITY_USER_FULL_UPDATED)

class CleanupBadge(FirstActivityAbstractBadge):
    def __init__(self):
        super(CleanupBadge, self).__init__(const.TYPE_ACTIVITY_CANCEL_VOTE)


class CivicDutyBadge(ActivityCountAbstractBadge):
    def __init__(self):
        super(CivicDutyBadge, self).__init__((const.TYPE_ACTIVITY_VOTE_DOWN, const.TYPE_ACTIVITY_VOTE_UP), settings.CIVIC_DUTY_VOTES)

class PunditBadge(ActivityCountAbstractBadge):
    def __init__(self):
        super(PunditBadge, self).__init__((const.TYPE_ACTIVITY_COMMENT_ANSWER, const.TYPE_ACTIVITY_COMMENT_QUESTION), settings.PUNDIT_COMMENT_COUNT)


class SelfLearnerBadge(CountableAbstractBadge):
    def __init__(self):

        def handler(instance):
            if instance.author_id == instance.question.author_id:
                self.award_badge(instance.author, instance)

        super(SelfLearnerBadge, self).__init__(Answer, 'vote_up_count', settings.SELF_LEARNER_UP_VOTES, handler)


class StrunkAndWhiteBadge(ActivityCountAbstractBadge):
    def __init__(self):
        super(StrunkAndWhiteBadge, self).__init__((const.TYPE_ACTIVITY_UPDATE_ANSWER, const.TYPE_ACTIVITY_UPDATE_QUESTION), settings.STRUNK_AND_WHITE_EDITS)


def is_user_first(self, post):
    return post.__class__.objects.filter(author=post.author).order_by('added_at')[0].id == post.id

class StudentBadge(CountableAbstractBadge):
    def __init__(self):
        def handler(instance):
            if is_user_first(instance):
                self.award_badge(instance.author, instance)

        super(StudentBadge, self).__init__(Question, 'vote_up_count', 1, handler)

class TeacherBadge(CountableAbstractBadge):
    def __init__(self):
        def handler(instance):
            if is_user_first(instance):
                self.award_badge(instance.author, instance)

        super(TeacherBadge, self).__init__(Answer, 'vote_up_count', 1, handler)


class AcceptedAndVotedAnswerAbstractBadge(AbstractBadge):
    def __init__(self, up_votes, handler):
        def handler(sender, **kwargs):
            if sender is const.TYPE_ACTIVITY_MARK_ANSWER:
                answer = kwargs['instance'].content_object
                accepted = True
                vote_count = answer.vote_up_count
            else:
                answer = kwargs['instance']
                accepted = answer.accepted
                vote_count = kwargs['new_value']

            if accepted and vote_count == up_votes:
                handler(answer)

        activity_record.connect(handler, sender=const.TYPE_ACTIVITY_MARK_ANSWER, weak=False)
        countable_update.connect(handler, sender=getattr(Answer, "vote_up_count_sender"), weak=False)


class EnlightenedBadge(AcceptedAndVotedAnswerAbstractBadge):
    def __init__(self):
        def handler(answer):
            self.award_badge(answer.author, answer, True)

        super(EnlightenedBadge, self).__init__(settings.ENLIGHTENED_UP_VOTES, handler)


class GuruBadge(AcceptedAndVotedAnswerAbstractBadge):
    def __init__(self):
        def handler(answer):
            self.award_badge(answer.author, answer)

        super(GuruBadge, self).__init__(40, handler)


class NecromancerBadge(AbstractBadge):
    def __init__(self):
        def handler(sender, **kwargs):
            if kwargs['new_value'] == settings.NECROMANCER_UP_VOTES:
                answer = kwargs['instance']

                if answer.added_at >= (answer.question.added_at + timedelta(days=60)):
                    self.award_badge(answer.author, answer)

        countable_update.connect(handler, sender=getattr(Answer, "vote_up_count_sender"), weak=False)


class TaxonomistBadge(AbstractBadge):
    def __init__(self):
        def handler(sender, **kwargs):
            map(parse_tag, Tag.objects.values('id', 'used_count').
                filter(id__in=map(lambda t: t.id, kwargs['tags'])))

        def parse_tag(tag):
            if tag['used_count'] == 50:
                tag = Tag.objects.get(id=tag['id'])
                self.award_badge(tag.created_by, tag)

        tags_update_use_count.connect(handler, weak=False)


class GeneralistTag(AbstractBadge):
    pass

class ExpertTag(AbstractBadge):
    pass

class YearlingTag(AbstractBadge):
    pass


            