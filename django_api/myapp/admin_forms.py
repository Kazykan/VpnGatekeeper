from django import forms


class ImportLegacyUsersForm(forms.Form):
    active_after = forms.DateField(
        label="Импортировать пользователей с подпиской активной ПОСЛЕ даты",
        required=True,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
