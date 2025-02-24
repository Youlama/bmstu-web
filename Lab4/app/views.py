import random
from datetime import datetime, timedelta
import uuid

from django.contrib.auth import authenticate
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .permissions import *
from .redis import session_storage
from .serializers import *
from .utils import identity_user, get_session


def get_draft_request(request):
    user = identity_user(request)

    if user is None:
        return None

    request = Request.objects.filter(owner=user).filter(status=1).first()

    return request


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'document_name',
            openapi.IN_QUERY,
            type=openapi.TYPE_STRING
        )
    ]
)
@api_view(["GET"])
def search_documents(request):
    document_name = request.GET.get("document_name", "")

    documents = Document.objects.filter(status=1)

    if document_name:
        documents = documents.filter(name__icontains=document_name)

    serializer = DocumentsSerializer(documents, many=True)

    return Response(serializer.data)


@api_view(["GET"])
def get_cart(request):
    draft_request = get_draft_request(request)

    resp = {
        "documents_count": DocumentRequest.objects.filter(request=draft_request).count() if draft_request else None,
        "draft_request_id": draft_request.pk if draft_request else None
    }

    return Response(resp)



@api_view(["GET"])
def get_document_by_id(request, document_id):
    if not Document.objects.filter(pk=document_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    document = Document.objects.get(pk=document_id)
    serializer = DocumentSerializer(document)

    return Response(serializer.data)


@swagger_auto_schema(method='put', request_body=DocumentSerializer)
@api_view(["PUT"])
@permission_classes([IsModerator])
def update_document(request, document_id):
    if not Document.objects.filter(pk=document_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    document = Document.objects.get(pk=document_id)

    serializer = DocumentSerializer(document, data=request.data)

    if serializer.is_valid(raise_exception=True):
        serializer.save()

    return Response(serializer.data)


@swagger_auto_schema(method='POST', request_body=DocumentAddSerializer)
@api_view(["POST"])
@permission_classes([IsModerator])
@parser_classes((MultiPartParser,))
def create_document(request):
    serializer = DocumentAddSerializer(data=request.data)

    serializer.is_valid(raise_exception=True)

    Document.objects.create(**serializer.validated_data)

    documents = Document.objects.filter(status=1)
    serializer = DocumentsSerializer(documents, many=True)

    return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([IsModerator])
def delete_document(request, document_id):
    if not Document.objects.filter(pk=document_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    document = Document.objects.get(pk=document_id)
    document.status = 2
    document.save()

    document = Document.objects.filter(status=1)
    serializer = DocumentSerializer(document, many=True)

    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_document_to_request(req, document_id):
    if not Document.objects.filter(pk=document_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    document = Document.objects.get(pk=document_id)

    draft_request = get_draft_request(req)

    if draft_request is None:
        draft_request = Request.objects.create()
        draft_request.date_created = timezone.now()
        draft_request.owner = identity_user(req)
        draft_request.save()

    if DocumentRequest.objects.filter(request=draft_request, document=document).exists():
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    item = DocumentRequest.objects.create()
    item.request = draft_request
    item.document = document
    item.save()

    serializer = RequestSerializer(draft_request)
    return Response(serializer.data["documents"])


@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter('image', openapi.IN_FORM, type=openapi.TYPE_FILE),
    ]
)
@api_view(["POST"])
@permission_classes([IsModerator])
@parser_classes((MultiPartParser,))
def update_document_image(request, document_id):
    if not Document.objects.filter(pk=document_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    document = Document.objects.get(pk=document_id)

    image = request.data.get("image")

    if image is None:
        return Response(status.HTTP_400_BAD_REQUEST)

    document.image = image
    document.save()

    serializer = DocumentSerializer(document)

    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'status',
            openapi.IN_QUERY,
            type=openapi.TYPE_NUMBER
        ),
        openapi.Parameter(
            'date_formation_start',
            openapi.IN_QUERY,
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'date_formation_end',
            openapi.IN_QUERY,
            type=openapi.TYPE_STRING
        )
    ]
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search_requests(request):
    status_id = int(request.GET.get("status", 0))
    date_formation_start = request.GET.get("date_formation_start")
    date_formation_end = request.GET.get("date_formation_end")

    requests = Request.objects.exclude(status__in=[1, 5])

    user = identity_user(request)
    if not user.is_superuser:
        requests = requests.filter(owner=user)

    if status_id > 0:
        requests = requests.filter(status=status_id)

    if date_formation_start and parse_datetime(date_formation_start):
        requests = requests.filter(date_formation__gte=parse_datetime(date_formation_start) - timedelta(days=1))

    if date_formation_end and parse_datetime(date_formation_end):
        requests = requests.filter(date_formation__lte=parse_datetime(date_formation_end) + timedelta(days=1))

    serializer = RequestsSerializer(requests, many=True)

    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_request_by_id(request, request_id):
    user = identity_user(request)

    if not Request.objects.filter(pk=request_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    request = Request.objects.get(pk=request_id)

    if not user.is_superuser and request.owner != user:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = RequestSerializer(request)

    return Response(serializer.data)


@swagger_auto_schema(method='put', request_body=RequestSerializer)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_request(req, request_id):
    user = identity_user(req)

    if not Request.objects.filter(pk=request_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    request = Request.objects.get(pk=request_id)
    serializer = RequestSerializer(request, data=req.data, partial=True)

    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_status_user(req, request_id):
    user = identity_user(req)

    if not Request.objects.filter(pk=request_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    request = Request.objects.get(pk=request_id)

    if request.status != 1:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    request.status = 2
    request.date_formation = timezone.now()
    request.save()

    serializer = RequestSerializer(request)

    return Response(serializer.data)


@swagger_auto_schema(
    method='put',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'status': openapi.Schema(type=openapi.TYPE_NUMBER),
        }
    )
)
@api_view(["PUT"])
@permission_classes([IsModerator])
def update_status_admin(req, request_id):
    if not Request.objects.filter(pk=request_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    request_status = int(req.data["status"])

    if request_status not in [3, 4]:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    request = Request.objects.get(pk=request_id)

    if request.status != 2:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def generate_document_number(number_length):
        new_number = ''
        for i in range(number_length):
            new_number += str(random.randint(0, 9))
        return int(new_number)

    if request_status == 3:
        for document in DocumentRequest.objects.filter(request=request):
            document.new_document_number = generate_document_number(document.number_length)
            document.save()

    request.status = request_status
    request.date_complete = timezone.now()
    request.moderator = identity_user(request)
    request.save()

    serializer = RequestSerializer(request)

    return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_request(req, request_id):
    user = identity_user(req)

    if not Request.objects.filter(pk=request_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    request = Request.objects.get(pk=request_id)

    if request.status != 1:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    request.status = 5
    request.save()

    return Response(status=status.HTTP_200_OK)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_document_from_request(req, request_id, document_id):
    user = identity_user(req)

    if not Request.objects.filter(pk=request_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    if not DocumentRequest.objects.filter(request_id=request_id, document_id=document_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    item = DocumentRequest.objects.get(request_id=request_id, document_id=document_id)
    item.delete()

    request = Request.objects.get(pk=request_id)

    serializer = RequestSerializer(request)
    documents = serializer.data["documents"]

    return Response(documents)


@swagger_auto_schema(method='PUT', request_body=DocumentRequestSerializer)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_document_in_request(req, request_id, document_id):
    user = identity_user(req)

    if not Request.objects.filter(pk=request_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    if not DocumentRequest.objects.filter(document_id=document_id, request_id=request_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    item = DocumentRequest.objects.get(document_id=document_id, request_id=request_id)

    serializer = DocumentRequestSerializer(item, data=req.data, partial=True)

    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)


@swagger_auto_schema(method='post', request_body=UserLoginSerializer)
@api_view(["POST"])
def login(req):
    serializer = UserLoginSerializer(data=req.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

    user = authenticate(**serializer.data)
    if user is None:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    session_id = str(uuid.uuid4())
    session_storage.set(session_id, user.id)

    serializer = UserSerializer(user)
    response = Response(serializer.data, status=status.HTTP_200_OK)
    response.set_cookie("session_id", session_id, samesite="lax")

    return response


@swagger_auto_schema(method='post', request_body=UserRegisterSerializer)
@api_view(["POST"])
def register(req):
    serializer = UserRegisterSerializer(data=req.data)

    if not serializer.is_valid():
        return Response(status=status.HTTP_409_CONFLICT)

    user = serializer.save()

    session_id = str(uuid.uuid4())
    session_storage.set(session_id, user.id)

    serializer = UserSerializer(user)
    response = Response(serializer.data, status=status.HTTP_201_CREATED)
    response.set_cookie("session_id", session_id, samesite="lax")

    return response


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(req):
    session = get_session(req)
    session_storage.delete(session)

    response = Response(status=status.HTTP_200_OK)
    response.delete_cookie('session_id')

    return response


@swagger_auto_schema(method='PUT', request_body=UserProfileSerializer)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_user(req, user_id):
    if not User.objects.filter(pk=user_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    user = identity_user(req)

    if user.pk != user_id:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = UserSerializer(user, data=req.data, partial=True)
    if not serializer.is_valid():
        return Response(status=status.HTTP_409_CONFLICT)

    serializer.save()

    password = req.data.get("password", None)
    if password is not None and not user.check_password(password):
        user.set_password(password)
        user.save()

    return Response(serializer.data, status=status.HTTP_200_OK)
