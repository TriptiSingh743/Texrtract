from django.contrib import admin
from django.urls import path
from . import views
from .views import upload_image
from . import views

from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'), # This should be the default route
    path('document-type-selection/', views.document_type_selection, name='document_type_selection'),
    path('upload-page/', views.upload_page, name='upload_page'),
    path('api/upload/', upload_image, name='upload_image'),
    path('entities/', views.entities, name='entities'),
    path('contact/', views.contact_view, name='contact'),
    path('success/', views.success_view, name='success'),
    path('chatbot/', views.chatbot_view, name='chatbot_view'),
    
]
     




