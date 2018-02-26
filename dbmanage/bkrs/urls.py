from django.conf.urls import include, url
from django.contrib import admin
import views

urlpatterns = [
    url(r'^$', views.index, name='bkrs'),
    url(r'received/backup_info/$',views.received_backup_info,name='received_backup_info'),
    url(r'^backarchives/$', views.backarchives, name='backarchives'),
    url(r'^customer/$', views.customer, name='customer'),
    url(r'^customer_add/$', views.customer_add, name='customer_add'),
    url(r'^edit_backnode/(\d+)$', views.edit_backnode, name='edit_backnode'),
    url(r'^backnode/$', views.backnode, name='backnode'),
    url(r'^add_backnode/$', views.add_backnode, name='add_backnode'),
    url(r'^set_config/$', views.index, name='set_config'),
    url(r'^backfailed/$', views.failed_customer, name='backfailed'),
    url(r'^backup_statics/$', views.backup_statics, name='backup_statics'),
    url(r'^help/$', views.help, name='help'),
]
