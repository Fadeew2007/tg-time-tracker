from django import forms
from .models import WorkSession

class WorkSessionForm(forms.ModelForm):
    class Meta:
        model = WorkSession
        fields = "__all__"
        widgets = {
            "start_time": forms.DateInput(format="%d.%m.%Y", attrs={"type": "date"}),
            "end_time": forms.DateInput(format="%d.%m.%Y", attrs={"type": "date"}),
        }