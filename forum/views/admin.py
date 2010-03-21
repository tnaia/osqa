from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden, Http404
from django.template import RequestContext

from forum.settings.base import Setting
from forum.settings.forms import SettingsSetForm


def super_user_required(fn):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated() and request.user.is_superuser:
            return fn(request, *args, **kwargs)
        else:
            raise Http404

    return wrapper

def index(request):
    return settings_set(request, 'basic')

@super_user_required    
def settings_set(request, set_name):
    set = Setting.sets.get(set_name, None)

    if set is None:
        raise Http404

    if request.POST:
        form = SettingsSetForm(set, request.POST)

        if form.is_valid():
            form.save()

    else:
        form = SettingsSetForm(set)

    all_sets = sorted(Setting.sets.values(), lambda s1, s2: s1.weight - s2.weight)

    return render_to_response('osqaadmin/base.html', {
        'form': form,
        'sets': all_sets,
    }, context_instance=RequestContext(request))
