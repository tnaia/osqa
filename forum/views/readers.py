# encoding:utf-8
import datetime
import logging
from urllib import unquote
from django.conf import settings as django_settings
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden, Http404
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.template import RequestContext
from django.utils.html import *
from django.utils import simplejson
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse
from django.utils.datastructures import SortedDict
from django.views.decorators.cache import cache_page
from django.utils.http import urlquote  as django_urlquote
from django.template.defaultfilters import slugify

from forum.utils.html import sanitize_html
from markdown2 import Markdown
from forum.utils.diff import textDiff as htmldiff
from forum.forms import *
from forum.models import *
from forum.const import *
from forum.utils.forms import get_next_url
from forum.models.question import question_view

# used in index page
#refactor - move these numbers somewhere?
INDEX_PAGE_SIZE = 30
INDEX_AWARD_SIZE = 15
INDEX_TAGS_SIZE = 25
# used in tags list
DEFAULT_PAGE_SIZE = 60
# used in questions
QUESTIONS_PAGE_SIZE = 30
# used in answers
ANSWERS_PAGE_SIZE = 10

markdowner = Markdown(html4tags=True)

#system to display main content
def _get_tags_cache_json():#service routine used by views requiring tag list in the javascript space
    """returns list of all tags in json format
    no caching yet, actually
    """
    tags = Tag.objects.filter(deleted=False).all()
    tags_list = []
    for tag in tags:
        dic = {'n': tag.name, 'c': tag.used_count}
        tags_list.append(dic)
    tags = simplejson.dumps(tags_list)
    return tags


def index(request):
    return questions(request, template="index.html", sort='latest', path=reverse('questions'))

def unanswered(request):
    return questions(request, unanswered=True)

def questions(request, tagname=None, unanswered=False, template="questions.html", sort=None, path=None):
    pagesize = request.utils.page_size(QUESTIONS_PAGE_SIZE)
    page = int(request.GET.get('page', 1))

    questions = Question.objects.filter(deleted=False)

    if tagname is not None:
        questions = questions.filter(tags__name=unquote(tagname))

    if unanswered:
        questions = questions.filter(answer_accepted=False)

    if request.user.is_authenticated():
        questions = questions.filter(
                ~Q(tags__id__in=request.user.marked_tags.filter(user_selections__reason='bad')))

    #todo: improve this stuff
    if sort is None:
        sort = request.utils.sort_method('latest')
    else:
        request.utils.set_sort_method(sort)
    
    view_dic = {"latest":"-added_at", "active":"-last_activity_at", "hottest":"-answer_count", "mostvoted":"-score" }
    orderby = view_dic[sort]

    questions=questions.order_by(orderby)
    
    objects_list = Paginator(questions, pagesize)
    questions = objects_list.page(page)

    return render_to_response(template, {
        "questions" : questions,
        "author_name" : None,
        "questions_count" : objects_list.count,
        "tags_autocomplete" : _get_tags_cache_json(),
        "searchtag" : tagname,
        "is_unanswered" : unanswered,
        "context" : {
            'is_paginated' : True,
            'pages': objects_list.num_pages,
            'page': page,
            'has_previous': questions.has_previous(),
            'has_next': questions.has_next(),
            'previous': questions.previous_page_number(),
            'next': questions.next_page_number(),
            'base_url' : (path or request.path) + '?sort=%s&' % sort,
            'pagesize' : pagesize
        }}, context_instance=RequestContext(request))


def search(request): 
    if request.method == "GET" and "q" in request.GET:
        keywords = request.GET.get("q")
        search_type = request.GET.get("t")
        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1
        if keywords is None:
            return HttpResponseRedirect(reverse(index))
        if search_type == 'tag':
            return HttpResponseRedirect(reverse('tags') + '?q=%s&page=%s' % (keywords.strip(), page))
        elif search_type == "user":
            return HttpResponseRedirect(reverse('users') + '?q=%s&page=%s' % (keywords.strip(), page))
        elif search_type == "question":
            
            template_file = "questions.html"
            # Set flag to False by default. If it is equal to True, then need to be saved.
            pagesize_changed = False
            # get pagesize from session, if failed then get default value
            user_page_size = request.session.get("pagesize", QUESTIONS_PAGE_SIZE)
            # set pagesize equal to logon user specified value in database
            if request.user.is_authenticated() and request.user.questions_per_page > 0:
                user_page_size = request.user.questions_per_page

            try:
                page = int(request.GET.get('page', '1'))
                # get new pagesize from UI selection
                pagesize = int(request.GET.get('pagesize', user_page_size))
                if pagesize <> user_page_size:
                    pagesize_changed = True

            except ValueError:
                page = 1
                pagesize  = user_page_size

            # save this pagesize to user database
            if pagesize_changed:
                request.session["pagesize"] = pagesize
                if request.user.is_authenticated():
                    user = request.user
                    user.questions_per_page = pagesize
                    user.save()

            view_id = request.GET.get('sort', None)
            view_dic = {"latest":"-added_at", "active":"-last_activity_at", "hottest":"-answer_count", "mostvoted":"-score" }
            try:
                orderby = view_dic[view_id]
            except KeyError:
                view_id = "latest"
                orderby = "-added_at"

            def question_search(keywords, orderby):
                objects = Question.objects.filter(deleted=False).extra(where=['title like %s'], params=['%' + keywords + '%']).order_by(orderby)
                # RISK - inner join queries
                return objects.select_related();

            from forum.modules import get_handler

            question_search = get_handler('question_search', question_search)
            
            objects = question_search(keywords, orderby)

            objects_list = Paginator(objects, pagesize)
            questions = objects_list.page(page)

            # Get related tags from this page objects
            related_tags = []
            for question in questions.object_list:
                tags = list(question.tags.all())
                for tag in tags:
                    if tag not in related_tags:
                        related_tags.append(tag)

            #if is_search is true in the context, prepend this string to soting tabs urls
            search_uri = "?q=%s&page=%d&t=question" % ("+".join(keywords.split()),  page)

            return render_to_response(template_file, {
                "questions" : questions,
                "tab_id" : view_id,
                "questions_count" : objects_list.count,
                "tags" : related_tags,
                "searchtag" : None,
                "searchtitle" : keywords,
                "keywords" : keywords,
                "is_unanswered" : False,
                "is_search": True, 
                "search_uri":  search_uri, 
                "context" : {
                    'is_paginated' : True,
                    'pages': objects_list.num_pages,
                    'page': page,
                    'has_previous': questions.has_previous(),
                    'has_next': questions.has_next(),
                    'previous': questions.previous_page_number(),
                    'next': questions.next_page_number(),
                    'base_url' : request.path + '?t=question&q=%s&sort=%s&' % (keywords, view_id),
                    'pagesize' : pagesize
                }}, context_instance=RequestContext(request))
 
    else:
        return render_to_response("search.html", context_instance=RequestContext(request))


def tag(request, tag):#stub generates listing of questions tagged with a single tag
    return questions(request, tagname=tag)

def tags(request):#view showing a listing of available tags - plain list
    stag = ""
    is_paginated = True
    sortby = request.GET.get('sort', 'used')
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    if request.method == "GET":
        stag = request.GET.get("q", "").strip()
        if stag != '':
            objects_list = Paginator(Tag.objects.filter(deleted=False).exclude(used_count=0).extra(where=['name like %s'], params=['%' + stag + '%']), DEFAULT_PAGE_SIZE)
        else:
            if sortby == "name":
                objects_list = Paginator(Tag.objects.all().filter(deleted=False).exclude(used_count=0).order_by("name"), DEFAULT_PAGE_SIZE)
            else:
                objects_list = Paginator(Tag.objects.all().filter(deleted=False).exclude(used_count=0).order_by("-used_count"), DEFAULT_PAGE_SIZE)

    try:
        tags = objects_list.page(page)
    except (EmptyPage, InvalidPage):
        tags = objects_list.page(objects_list.num_pages)

    return render_to_response('tags.html', {
                                            "tags" : tags,
                                            "stag" : stag,
                                            "tab_id" : sortby,
                                            "keywords" : stag,
                                            "context" : {
                                                'is_paginated' : is_paginated,
                                                'pages': objects_list.num_pages,
                                                'page': page,
                                                'has_previous': tags.has_previous(),
                                                'has_next': tags.has_next(),
                                                'previous': tags.previous_page_number(),
                                                'next': tags.next_page_number(),
                                                'base_url' : reverse('tags') + '?sort=%s&' % sortby
                                            }
                                }, context_instance=RequestContext(request))

def get_answer_sort_order(request):
    view_dic = {"latest":"-added_at", "oldest":"added_at", "votes":"-score" }

    view_id = request.GET.get('sort', request.session.get('answer_sort_order', None))

    if view_id is None or not view_id in view_dic:
        view_id = "votes"

    if view_id != request.session.get('answer_sort_order', None):
        request.session['answer_sort_order'] = view_id

    return (view_id, view_dic[view_id])

def update_question_view_times(request, question):
    if not 'question_view_times' in request.session:
        request.session['question_view_times'] = {}

    last_seen = request.session['question_view_times'].get(question.id,None)
    updated_when, updated_who = question.get_last_update_info()

    if not last_seen or last_seen < updated_when:
        question.view_count = question.view_count + 1
        question_view.send(sender=update_question_view_times, instance=question, user=request.user)

    request.session['question_view_times'][question.id] = datetime.datetime.now()

def question(request, id, slug):
    question = get_object_or_404(Question, id=id)

    if slug != urlquote(slugify(question.title)):
        return HttpResponseRedirect(question.get_absolute_url())

    page = int(request.GET.get('page', 1))
    view_id, order_by = get_answer_sort_order(request)

    if question.deleted and not request.user.can_view_deleted_post(question):
        raise Http404

    answer_form = AnswerForm(question,request.user)
    answers = request.user.get_visible_answers(question)

    if answers is not None:
        answers = [a for a in answers.order_by("-accepted", order_by)
                   if not a.deleted or a.author == request.user]

    objects_list = Paginator(answers, ANSWERS_PAGE_SIZE)
    page_objects = objects_list.page(page)

    update_question_view_times(request, question)

    if request.user.is_authenticated():
        try:
            subscription = QuestionSubscription.objects.get(question=question, user=request.user)
        except:
            subscription = False
    else:
        subscription = False

    return render_to_response('question.html', {
        "question" : question,
        "answer" : answer_form,
        "answers" : page_objects.object_list,
        "tags" : question.tags.all(),
        "tab_id" : view_id,
        "similar_questions" : question.get_related_questions(),
        "subscription": subscription,
        "context" : {
            'is_paginated' : True,
            'pages': objects_list.num_pages,
            'page': page,
            'has_previous': page_objects.has_previous(),
            'has_next': page_objects.has_next(),
            'previous': page_objects.previous_page_number(),
            'next': page_objects.next_page_number(),
            'base_url' : request.path + '?sort=%s&' % view_id,
            'extend_url' : "#sort-top"
        }
        }, context_instance=RequestContext(request))


QUESTION_REVISION_TEMPLATE = ('<h1>%(title)s</h1>\n'
                              '<div class="text">%(html)s</div>\n'
                              '<div class="tags">%(tags)s</div>')
def question_revisions(request, id):
    post = get_object_or_404(Question, id=id)
    revisions = list(post.revisions.all())
    revisions.reverse()
    for i, revision in enumerate(revisions):
        revision.html = QUESTION_REVISION_TEMPLATE % {
            'title': revision.title,
            'html': sanitize_html(markdowner.convert(revision.text)),
            'tags': ' '.join(['<a class="post-tag">%s</a>' % tag
                              for tag in revision.tagnames.split(' ')]),
        }
        if i > 0:
            revisions[i].diff = htmldiff(revisions[i-1].html, revision.html)
        else:
            revisions[i].diff = QUESTION_REVISION_TEMPLATE % {
                'title': revisions[0].title,
                'html': sanitize_html(markdowner.convert(revisions[0].text)),
                'tags': ' '.join(['<a class="post-tag">%s</a>' % tag
                                 for tag in revisions[0].tagnames.split(' ')]),
            }
            revisions[i].summary = _('initial version') 
    return render_to_response('revisions_question.html', {
                              'post': post,
                              'revisions': revisions,
                              }, context_instance=RequestContext(request))

ANSWER_REVISION_TEMPLATE = ('<div class="text">%(html)s</div>')
def answer_revisions(request, id):
    post = get_object_or_404(Answer, id=id)
    revisions = list(post.revisions.all())
    revisions.reverse()
    for i, revision in enumerate(revisions):
        revision.html = ANSWER_REVISION_TEMPLATE % {
            'html': sanitize_html(markdowner.convert(revision.text))
        }
        if i > 0:
            revisions[i].diff = htmldiff(revisions[i-1].html, revision.html)
        else:
            revisions[i].diff = revisions[i].text
            revisions[i].summary = _('initial version')
    return render_to_response('revisions_answer.html', {
                              'post': post,
                              'revisions': revisions,
                              }, context_instance=RequestContext(request))

