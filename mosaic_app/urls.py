from django.conf.urls import url,include
from mosaic_app import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # url(r"login/$",views.login,name="login"),
    url(r"^create_mosaic/$",views.create_mosaic,name="create_mosaic"),
    # url(r"get_album_images/$",views.get_album_images,name="get_album_images"),
    # url(r"get_album_images/$",views.make_mosaic,name="make_mosaic"),
    url(r"logout/$", auth_views.LogoutView.as_view(), name="logout"),
    url(r"^my_page/$",views.my_page,name="my_page"),
    # url(r"^my_page/(?P<mosaic_id>[0-9]+)/$", views.full_screen, name="full_screen"),
    url(r"^my_page/(?P<mosaic_id>[0-9]+)/$", views.full_screen, name="full_screen"),
    url(r"^top_page/$",views.top_page,name="top_page"),
]