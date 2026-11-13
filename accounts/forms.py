from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password


class StudentAccountCreationForm(forms.Form):
    MATCH_ERROR = "We couldn't verify those details. Check them with your registrar and try again."

    student_id = forms.CharField(max_length=20, label="Student ID")
    email = forms.EmailField(label="Student email address")
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["student_id"].widget.attrs["autocomplete"] = "off"
        self.fields["email"].widget.attrs["autocomplete"] = "email"

    def clean_student_id(self):
        return self.cleaned_data["student_id"].strip().upper()

    def clean_email(self):
        return self.cleaned_data["email"].strip().casefold()

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        email = cleaned_data.get("email")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "The passwords do not match.")
        if password1:
            user_model = get_user_model()
            candidate = user_model(username=email or "", email=email or "")
            try:
                validate_password(password1, user=candidate)
            except forms.ValidationError as error:
                self.add_error("password1", error)
        return cleaned_data
