from django.contrib import admin
from django.urls import path
from books import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Public Reader URLs
    path('', views.home, name='home'),
    path('user-all/', views.user_all, name='user_all'),
    path('book/<int:id>/', views.book_detail, name='book_detail'),
    path('view-pdf/<int:id>/', views.stream_pdf, name='stream_pdf'),
    path('download-pdf/<int:id>/', views.download_pdf, name='download_pdf'),
    path('api/quick-view/<int:id>/', views.quick_view_api, name='quick_view_api'),

    # Admin Management URLs
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('all-books/', views.all_books, name='all_books'),
    path('add-book/', views.add_book, name='add_book'),
    path('update-book/<int:id>/', views.update_book, name='update_book'),
    path('delete-book/<int:id>/', views.delete_book, name='delete_book'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
