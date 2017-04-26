from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='index.html')),
    url(r'^trainData/', views.trainData, name='trainData'),
    url(r'^classifyInstance/', views.classifyInstance, name='classifyInstance'),
    url(r'^getZillowData/', views.getZillowData, name='getZillowData'),
    url(r'^getWalkScore/', views.getWalkScoreAPI, name='getWalkScore'),
]
