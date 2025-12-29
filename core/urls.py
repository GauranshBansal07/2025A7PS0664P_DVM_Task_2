from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, api_views

urlpatterns = [
    path('', views.home, name='home'), 
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('buy/', views.buy_ticket, name='buy_ticket'),
    path('wallet/', views.add_funds, name='add_funds'),
    path('my-tickets/', views.my_tickets, name='my_tickets'),
    path('ticket/<uuid:ticket_id>/', views.ticket_confirmation, name='ticket_confirmation'),
    path('ticket/cancel/<uuid:ticket_id>/', views.cancel_ticket, name='cancel_ticket'),
    path('scanner/', views.scanner_view, name='scanner'),
    path('api/scan/', api_views.scan_ticket, name='api_scan'),
    path('admin-create-ticket/', views.admin_create_ticket, name='admin_create_ticket'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/password/', 
         auth_views.PasswordChangeView.as_view(template_name='core/change_password.html', success_url='/profile/password/done/'), 
         name='password_change'),
    path('profile/password/done/', 
         auth_views.PasswordChangeDoneView.as_view(template_name='core/change_password_done.html'), 
         name='password_change_done'),
    path('buy/verify/', views.verify_otp_page, name='verify_otp_page'),
]