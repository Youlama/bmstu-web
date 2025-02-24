from django.urls import path
from .views import *

urlpatterns = [
    # Набор методов для услуг
    path('api/documents/', search_documents),  # GET
    path('api/documents/<int:document_id>/', get_document_by_id),  # GET
    path('api/documents/<int:document_id>/update/', update_document),  # PUT
    path('api/documents/<int:document_id>/update_image/', update_document_image),  # POST
    path('api/documents/<int:document_id>/delete/', delete_document),  # DELETE
    path('api/documents/create/', create_document),  # POST
    path('api/documents/<int:document_id>/add_to_request/', add_document_to_request),  # POST

    # Набор методов для корзины
    path('api/cart/', get_cart),  # GET

    # Набор методов для заявок
    path('api/requests/', search_requests),  # GET
    path('api/requests/<int:request_id>/', get_request_by_id),  # GET
    path('api/requests/<int:request_id>/update/', update_request),  # PUT
    path('api/requests/<int:request_id>/update_status_user/', update_status_user),  # PUT
    path('api/requests/<int:request_id>/update_status_admin/', update_status_admin),  # PUT
    path('api/requests/<int:request_id>/delete/', delete_request),  # DELETE

    # Набор методов для м-м
    path('api/requests/<int:request_id>/update_document/<int:document_id>/', update_document_in_request),  # PUT
    path('api/requests/<int:request_id>/delete_document/<int:document_id>/', delete_document_from_request),  # DELETE

    # Набор методов для аутентификации и авторизации
    path("api/users/register/", register),  # POST
    path("api/users/login/", login),  # POST
    path("api/users/logout/", logout),  # POST
    path("api/users/<int:user_id>/update/", update_user)  # PUT
]
