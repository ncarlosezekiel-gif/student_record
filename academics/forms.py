from django import forms
from .models import Enrollment, Grade


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ("student", "academic_year", "semester", "course", "section", "year_level", "status")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-select" if isinstance(field.widget, forms.Select) else "form-control"


class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ("enrollment", "assignment", "grade", "remarks")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
