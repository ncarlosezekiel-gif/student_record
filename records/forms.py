from django import forms
from django.forms import inlineformset_factory
from .models import Guardian, Student


class DateInput(forms.DateInput):
    input_type = "date"


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        exclude = ("student_id", "user", "created_at", "updated_at")
        widgets = {"date_of_birth": DateInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        for name in ("gender", "status"):
            self.fields[name].widget.attrs["class"] = "form-select"


class GuardianForm(forms.ModelForm):
    class Meta:
        model = Guardian
        fields = ("name", "relationship", "contact_number", "email", "address")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


GuardianFormSet = inlineformset_factory(
    Student,
    Guardian,
    form=GuardianForm,
    extra=1,
    can_delete=True,
)
