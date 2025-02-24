from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, User
from django.db import models


class Document(models.Model):
    STATUS_CHOICES = (
        (1, 'Действует'),
        (2, 'Удалена'),
    )

    name = models.CharField(max_length=100, verbose_name="Название")
    description = models.TextField(max_length=500, verbose_name="Описание",)
    status = models.IntegerField(choices=STATUS_CHOICES, default=1, verbose_name="Статус")
    image = models.ImageField(verbose_name="Фото", blank=True, null=True)

    prod_period = models.IntegerField(verbose_name="Срок изготовления")
    replace_period = models.IntegerField(verbose_name="Срок замены", blank=True, null=True)
    number_length = models.IntegerField(verbose_name="Длинна номера документа")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Коды"
        db_table = "documents"
        ordering = ('pk', )


class Request(models.Model):
    STATUS_CHOICES = (
        (1, 'Введён'),
        (2, 'В работе'),
        (3, 'Завершен'),
        (4, 'Отклонен'),
        (5, 'Удален')
    )

    status = models.IntegerField(choices=STATUS_CHOICES, default=1, verbose_name="Статус")
    date_created = models.DateTimeField(verbose_name="Дата создания", blank=True, null=True)
    date_formation = models.DateTimeField(verbose_name="Дата формирования", blank=True, null=True)
    date_complete = models.DateTimeField(verbose_name="Дата завершения", blank=True, null=True)

    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="Создатель", related_name='owner', null=True)
    moderator = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="Сотрудник", related_name='moderator', blank=True,  null=True)

    reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return "Заявка №" + str(self.pk)

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        db_table = "requests"
        ordering = ('-date_formation', )


class DocumentRequest(models.Model):
    document = models.ForeignKey(Document, on_delete=models.DO_NOTHING, blank=True, null=True)
    request = models.ForeignKey(Request, on_delete=models.DO_NOTHING, blank=True, null=True)
    comment = models.TextField(default="Комментарий", verbose_name="Комментарий")
    new_document_number = models.BigIntegerField(blank=True, null=True)

    def __str__(self):
        return "м-м №" + str(self.pk)

    class Meta:
        verbose_name = "м-м"
        verbose_name_plural = "м-м"
        db_table = "document_request"
        ordering = ('pk', )
        constraints = [
            models.UniqueConstraint(fields=['document', 'request'], name="document_request_constraint")
        ]
