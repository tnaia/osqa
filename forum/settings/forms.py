from django import forms
from base import Setting, StringSetting, IntegerSetting, BoolSetting

class SettingsSetForm(forms.Form):
    def __init__(self, set, data=None, *args, **kwargs):
        if data is None:
            data = dict([(setting.name, setting.value) for setting in set])

        super(SettingsSetForm, self).__init__(data, *args, **kwargs)

        for setting in set:
            if isinstance(setting, StringSetting):
                field = forms.CharField(**setting.field_context)
            elif isinstance(setting, IntegerSetting):
                field = forms.IntegerField(**setting.field_context)
            elif isinstance(setting, BoolSetting):
                field = forms.BooleanField(**setting.field_context)
            else:
                field = forms.CharField(**setting.field_context)

            self.fields[setting.name] = field

        self.set = set

    def save(self):
        for setting in self.set:
            setting.set_value(self.cleaned_data[setting.name])


