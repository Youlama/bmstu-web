import os

from rest_framework import serializers

from .models import *


class DocumentsSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    def get_image(self, document):
        if document.image:
            return document.image.url.replace("minio", os.getenv("IP_ADDRESS"), 1)

        return f"http://{os.getenv("IP_ADDRESS")}:9000/images/default.png"

    class Meta:
        model = Document
        fields = ("id", "name", "status", "prod_period", "image")


class DocumentSerializer(DocumentsSerializer):
    class Meta:
        model = Document
        fields = "__all__"


class DocumentAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ("name", "description", "prod_period", "image")


class RequestsSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    moderator = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Request
        fields = "__all__"


class RequestSerializer(RequestsSerializer):
    documents = serializers.SerializerMethodField()

    def get_documents(self, request):
        items = DocumentRequest.objects.filter(request=request)

        if request.status == 3:
            return [DocumentItemSerializerWithCalc(item.document, context={"comment": item.comment, "new_document_number": item.new_document_number}).data for item in items]

        return [DocumentItemSerializer(item.document, context={"comment": item.comment}).data for item in items]


class DocumentItemSerializer(DocumentSerializer):
    comment = serializers.SerializerMethodField()

    def get_comment(self, _):
        return self.context.get("comment")


class DocumentItemSerializerWithCalc(DocumentItemSerializer):
    new_document_number = serializers.SerializerMethodField()

    def get_new_document_number(self, _):
        return self.context.get("new_document_number")


class DocumentRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentRequest
        fields = "__all__"

    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', "is_superuser")


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'username')
        write_only_fields = ('password',)
        read_only_fields = ('id',)

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data['username']
        )

        user.set_password(validated_data['password'])
        user.save()

        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)


class UserProfileSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    email = serializers.CharField(required=False)
    password = serializers.CharField(required=False)
