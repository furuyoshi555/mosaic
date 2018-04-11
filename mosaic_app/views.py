from django.shortcuts import render,render_to_response,redirect,get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django import forms
from django.core.files import File
from django.core.files.base import ContentFile
from bs4 import BeautifulSoup
import datetime
import glob
import io
from io import BytesIO
import json
from mosaic_app.models import MainImageInfo,MosaicArtInfo
from mosaic_app.forms import AuthorizationTokenForm,MainImageForm,AlbumNumberForm
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
import os
from PIL import Image,ImageStat
import requests
import shutil
import statistics as st
import urllib.request
import webbrowser
import xmltodict
from django.core.files.images import ImageFile



# Create your views here.
def index(request):
    return render(request,"mosaic_app/index.html")


def login(request):
    return render(request,"mosaic_app/login.html") 

def top_page(request):
    # userid = social.uid
    return render(request,"mosaic_app/top_page.html") 

@login_required
def logout(request):
    logout(request)
    return render_to_response("logout.html", context_instance=RequestContext)

@login_required
def create_mosaic(request):
    return render(request,"mosaic_app/create_mosaic.html")

@login_required
def my_page(request):
    user_id = request.user.id
    main_images = MainImageInfo.objects.filter(user_id=user_id)
    mosaic_arts = MosaicArtInfo.objects.filter(user_id=user_id)

    return render(request,"mosaic_app/my_page.html",{
                                                    "main_images":main_images,
                                                    "mosaic_arts":mosaic_arts})

def full_screen(request,mosaic_id):
    full_screen_mosaic_art = get_object_or_404(MosaicArtInfo,pk=mosaic_id)
    return render(request,'mosaic_app/full_screen.html',{'full_screen_mosaic_art':full_screen_mosaic_art})


@login_required
def create_mosaic(request):

    DOT_AREA_WIDTH_SIDE = 3
    DOT_AREA_HEIGHT_SIDE = 2
    # THUMBNAIL_WIDTH_SIDE = 240
    THUMBNAIL_WIDTH_SIDE = 30
    # THUMBNAIL_HEIGHT_SIDE = 160
    THUMBNAIL_HEIGHT_SIDE = 20
    # 2つの色(R,G,B)の間の最大の距離
    # MAX_COLOR_DISTANCE = 255 ** 2 * 3
    # CSVファイル中のカラムの意味づけ
    # POS_NAME = 0
    # POS_RED = 1
    # POS_GREEN = 2
    # POS_BLUE = 3
    
    
    main_image = MainImageForm()
    form = AuthorizationTokenForm()
    album_num = AlbumNumberForm()

    now=datetime.datetime.now()
    datetime_for_path = str(now.year)+str(now.month)+str(now.day)+str(now.hour)+str(now.minute)+str(now.second)

    

    # user_id = request.user.id
    # request.session["user-id"] = user_id

    user_choice_album_title = ""
    # get access_token
    flow = flow_from_clientsecrets(
        'static/secret/client_secrets.json',
        scope='https://picasaweb.google.com/data/',
        redirect_uri="urn:ietf:wg:oauth:2.0:oob"
        )

    auth_uri = flow.step1_get_authorize_url()
    

    album_dict = []
    album_list = []
    if request.method == "POST":
            form = AuthorizationTokenForm(data=request.POST)
            if form.is_valid():
                token = form.cleaned_data["authorization_token"] 
                credentials = flow.step2_exchange(token)
                storage = Storage('static/secret/credentials')
                storage.put(credentials)
                with open("static/secret/credentials") as json_file:
                    load = json.load(json_file)
                
                access_token = load["access_token"]
                request.session["access_token"] = access_token

                user_id = request.user.email

                url = 'https://picasaweb.google.com/data/feed/api/user/{}'.format(user_id)
                head = {'Authorization': 'OAuth {}'.format(access_token)}
                response = requests.get(url, headers=head)
                text = response.text
                # print(text)
                jan = xmltodict.parse(text)
                json_dict = json.loads(json.dumps(jan, indent=4))
                album_count = len(json_dict["feed"]["entry"])
                
                for a in range(album_count):
                    title = json_dict["feed"]["entry"][a]['media:group']['media:title']['#text']
                    title_image_url = json_dict["feed"]["entry"][a]['media:group']['media:content']['@url']
                    album_id = json_dict["feed"]["entry"][a]['gphoto:id']
                    a_list = [a-1,title,title_image_url,album_id,]
                    album_list.append(a_list)
                del(album_list[0])
                request.session["album_list"] = album_list
    else:
        form = AuthorizationTokenForm()
  
        
    if request.method == "POST":
            main_image = MainImageForm(data=request.POST)
            album_num = AlbumNumberForm(data=request.POST)

            if main_image.is_valid() and album_num.is_valid():
                user_choice_album_num = album_num.cleaned_data["album_num"]
                # print(type(main_image["main_image"]))
                # print(main_image["main_image"])
                # request.session["main_image"] = main_image["main_image"]
                new_image = main_image.save(commit=False)
                new_image.main_image = request.FILES["main_image"]
                # request.session["main_image"] = request.FILES["main_image"]
                # request.session["main_image"] = new_image.main_image
                new_image.user_id = request.user.id
                new_image.save()
                if "album_list" in request.session:
                    album_list = request.session["album_list"]
                user_choice_album_id = album_list[int(user_choice_album_num)][3]
                user_choice_album_title = album_list[int(user_choice_album_num)][1]


                user_id = request.user.email
                album_url = 'https://picasaweb.google.com/data/feed/api/user/{}/album/{}'.format(user_id, user_choice_album_id)
                if "access_token" in request.session:
                    access_token = request.session["access_token"]
                head = {'Authorization': 'OAuth {}'.format(access_token)}
                response = requests.get(album_url, headers=head)
                images_xml_data = response.text
                x_dict = xmltodict.parse(images_xml_data)
                json_data = json.loads(json.dumps(x_dict, indent=4))
                album_image_count = len(json_data["feed"]["entry"])
                os.mkdir("media/thumbnail_images/"+ datetime_for_path)
                new_dir_path = "media/thumbnail_images/"+ datetime_for_path + "/"
                for i in range(album_image_count):
                    images_urls = json_data["feed"]["entry"][i]['media:group']['media:content']['@url']
                    base = os.path.basename(images_urls)
                    dst_path = os.path.join(new_dir_path, base)
                    f = io.BytesIO(urllib.request.urlopen(images_urls).read())
                    img = Image.open(f)
                    resize_im = img.resize((int(300),int(200)))
                    resize_im.save(new_dir_path + str(i) + ".jpg","JPEG")

                data_list = []
                for image_name in os.listdir(new_dir_path):
                    if not image_name.endswith(".jpg"):
                        continue
                    im = Image.open(new_dir_path + image_name)
                    im_width, im_height = im.size
                    red, green, blue = average_color_in_range(im, 0, 0, im_width, im_height)
                    data_list.append([image_name, red, green, blue])

                color_data = data_list


                main_image = MainImageInfo.objects.last()
                main_image = main_image.main_image
                
                image = Image.open(main_image)
                icon_im = image.resize((int(300),int(200)))

                        # icon_im = Image.open(main_image)
                        # 対象画像の横幅と縦幅
                icon_im_width, icon_im_height = icon_im.size

                mosaic_icon_im = Image.new('RGBA', (3000, 2000))

                # 貼り付け作業
                for left in range(0, icon_im_width, DOT_AREA_WIDTH_SIDE):
                    for top in range(0, icon_im_height, DOT_AREA_HEIGHT_SIDE):
                        average_color = average_color_in_range(icon_im, left, top,
                                                            left+DOT_AREA_WIDTH_SIDE, top+DOT_AREA_HEIGHT_SIDE)
                        if len(average_color) != 3:
                            continue

                        filename = similar_color_filename(average_color, color_data)
                            # 距離最小のファイルを縮小して1600×1600の画像に貼り付け
                        area_im = Image.open(new_dir_path + filename)
                        area_im.thumbnail((THUMBNAIL_WIDTH_SIDE, THUMBNAIL_HEIGHT_SIDE))
                        mosaic_icon_im.paste(area_im, (left//DOT_AREA_WIDTH_SIDE * THUMBNAIL_WIDTH_SIDE,
                                                                top//DOT_AREA_HEIGHT_SIDE * THUMBNAIL_HEIGHT_SIDE))

                mosaic_icon_im.save("static/mosaic_app/images/mosaic_arts/" + datetime_for_path + ".png", "PNG")
                shutil.rmtree(new_dir_path)


                m = MosaicArtInfo.objects.create(user_id=request.user.id)
                g = ImageFile(open("static/mosaic_app/images/mosaic_arts/" + datetime_for_path + ".png","rb"))
                m.mosaic_art.save( datetime_for_path +'.png',g)
                        # m.user_id.save(request.user.id)
                m.save()
                return redirect(my_page)  
                  
    else:
        image_form = MainImageForm()
        album_num = AlbumNumberForm()
    
    return render(request,"mosaic_app/create_mosaic.html",{
                                                            "album_list":album_list,
                                                            "auth_uri":auth_uri,
                                                            "form":form,
                                                            "main_image":main_image,
                                                            "album_num":album_num
                                                            })


# 平均色の計算

def average_color_in_range(icon_im,left,top,right,bottom):

    if left >= right:
        print("left",left,">= right",right)
        return ()

    if top >= bottom:
        print("bottom",bottom,">= top",top)
        return ()
    
    im_crop = icon_im.crop((left,top,right,bottom))
    im_mean = ImageStat.Stat(im_crop).mean
    red = round(im_mean[0])
    green = round(im_mean[1])
    blue = round(im_mean[2])
    return (red,green,blue)


# 色の誤差

def color_distance(RGB1, RGB2):
    d2_r = (RGB1[0] - RGB2[0]) ** 2
    d2_g = (RGB1[1] - RGB2[1]) ** 2
    d2_b = (RGB1[2] - RGB2[2]) ** 2
    return d2_r + d2_g + d2_b



# 色の差が最小になるファイルの作成

def similar_color_filename(average_color, color_data):
    distance = 255 ** 2 * 3
    filename = ""
    
    for color in color_data:
        sample_color = (color[1], color[2], color[3])
        d = color_distance(average_color, sample_color)
        if d < distance:
            distance = d
            filename = color[0]
    return filename

