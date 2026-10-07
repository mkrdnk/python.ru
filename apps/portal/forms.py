from django import forms
from apps.portal.models import Contribution


class SubscribeForm(forms.Form):
    email = forms.EmailField(label='Электронная почта', max_length=254,
                            widget=forms.EmailInput(attrs={'placeholder': 'you@example.com', 'autocomplete': 'email'}))
    website = forms.CharField(required=False, widget=forms.HiddenInput)


class ContributionForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Contribution
        fields = ['kind', 'title', 'name', 'email', 'url', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 6})}
