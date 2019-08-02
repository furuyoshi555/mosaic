from django import forms
from django.contrib.admin import widgets
from mosaic_app.models import MainImageInfo


class AuthorizationTokenForm(forms.Form):
    
    def __init__(self, *args, **kwargs):
        super(AuthorizationTokenForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    class Meta():
        pass

    authorization_token = forms.CharField(label="Tokenを入力")
    # image = forms.()



class MainImageForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(MainImageForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control-file"

    class Meta():
        model = MainImageInfo
        fields = ("main_image",)
        labels = {"main_image":"対象画像"}



class AlbumNumberForm(forms.Form):
    
    def __init__(self, *args, **kwargs):
        super(AlbumNumberForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


    class Meta():
        pass

    album_num = forms.CharField(label="アルバム番号")