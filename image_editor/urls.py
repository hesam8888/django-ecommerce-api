from django.urls import path
from . import views

app_name = 'image_editor'

urlpatterns = [
    path('', views.editor_home, name='home'),
    path('<int:image_id>/', views.edit_image, name='edit_image'),
    path('<int:image_id>/rotate/', views.rotate_image, name='rotate_image'),
    path('<int:image_id>/crop/', views.crop_image, name='crop_image'),
    path('<int:image_id>/download/', views.download_image, name='download_image'),
    path('update/<int:image_id>/', views.update_image, name='update_image'),
] 