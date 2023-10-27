from django import forms
from .models import BlockModel


class BlockModelForm(forms.ModelForm):
    class Meta:
        model = BlockModel
        fields = ("program_content",)
