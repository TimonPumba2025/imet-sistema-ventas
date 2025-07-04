"""
URL configuration for imet project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from entidad.views import login,logout
from django.contrib.auth import views as auth_views

handler404 = 'entidad.views.mi_error_404'  # si tu vista está en entidad/views.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('entidad.urls')),
    # path('login/', login.as_view(redirect_authenticated_user=True, template_name='registration/login.html')),

    #path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout')
]
