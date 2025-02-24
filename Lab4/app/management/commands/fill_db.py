from django.conf import settings
from django.core.management.base import BaseCommand
from minio import Minio

from .utils import *
from app.models import *


def add_users():
    User.objects.create_user("user", "user@user.com", "1234", first_name="user", last_name="user")
    User.objects.create_superuser("root", "root@root.com", "1234", first_name="root", last_name="root")

    for i in range(1, 10):
        User.objects.create_user(f"user{i}", f"user{i}@user.com", "1234", first_name=f"user{i}", last_name=f"user{i}")
        User.objects.create_superuser(f"root{i}", f"root{i}@root.com", "1234", first_name=f"user{i}", last_name=f"user{i}")


def add_documents():
    Document.objects.create(
        name="Паспорт РФ",
        description="Старый паспорт, свидетельство о браке или разводе, смене ФИО или даты рождения, фото 35 × 45 мм, чек об оплате госпошлины.",
        prod_period=10,
        replace_period=90,
        number_length=7,
        image="1.png"
    )

    Document.objects.create(
        name="Загранпаспорт",
        description="Ранее выданные загранпаспорта — при наличии, паспорт РФ",
        prod_period=30,
        number_length=8,
        image="2.png"
    )

    Document.objects.create(
        name="Водительское удостоверение",
        description="Водительское удостоверение, паспорт РФ",
        prod_period=1,
        number_length=6,
        image="3.png"
    )

    Document.objects.create(
        name="Полис ОМС",
        description="Паспорт РФ, старый полис ОМС",
        prod_period=45,
        replace_period=30,
        number_length=5,
        image="4.png"
    )

    Document.objects.create(
        name="ИНН",
        description="Паспорт РФ",
        prod_period=5,
        number_length=6,
        image="5.png"
    )

    client = Minio(settings.MINIO_ENDPOINT,
                   settings.MINIO_ACCESS_KEY,
                   settings.MINIO_SECRET_KEY,
                   secure=settings.MINIO_USE_HTTPS)

    for i in range(1, 7):
        client.fput_object(settings.MINIO_MEDIA_FILES_BUCKET, f'{i}.png', f"app/static/images/{i}.png")

    client.fput_object(settings.MINIO_MEDIA_FILES_BUCKET, 'default.png', "app/static/images/default.png")


def add_requests():
    users = User.objects.filter(is_staff=False)
    moderators = User.objects.filter(is_staff=True)
    documents = Document.objects.all()

    for _ in range(30):
        status = random.randint(2, 5)
        owner = random.choice(users)
        add_request(status, documents, owner, moderators)

    add_request(1, documents, users[0], moderators)
    add_request(2, documents, users[0], moderators)
    add_request(3, documents, users[0], moderators)
    add_request(4, documents, users[0], moderators)
    add_request(5, documents, users[0], moderators)

    for _ in range(10):
        status = random.randint(2, 5)
        add_request(status, documents, users[0], moderators)


def add_request(status, documents, owner, moderators):
    request = Request.objects.create()
    request.status = status

    if status in [3, 4]:
        request.moderator = random.choice(moderators)
        request.date_complete = random_date()
        request.date_formation = request.date_complete - random_timedelta()
        request.date_created = request.date_formation - random_timedelta()
    else:
        request.date_formation = random_date()
        request.date_created = request.date_formation - random_timedelta()

    request.reason = "Веская причина смены фамилии"

    request.owner = owner

    for document in random.sample(list(documents), 3):
        item = DocumentRequest(
            request=request,
            document=document,
            comment="Комментарий",
            new_document_number=generate_document_number(document.number_length) if request.status == 3 else None
        )
        item.save()

    request.save()


def generate_document_number(number_length):
    new_number = ''
    for i in range(number_length):
        new_number += str(random.randint(0,9))
    return int(new_number)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        add_users()
        add_documents()
        add_requests()
