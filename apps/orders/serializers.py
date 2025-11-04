from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Order, OrderItem

User = get_user_model()

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id","product","qty","price"]

class OrderSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)

    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ["id","user","status","items","created_at","updated_at"]
        read_only_fields = ["id","created_at","updated_at"]

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        request = self.context["request"]
        user = validated_data.pop("user", None)

        if user is None or not request.user.is_staff:
            user = request.user

        order = Order.objects.create(user=user, **validated_data)
        for it in items:
            OrderItem.objects.create(order=order, **it)
        return order

    def update(self, instance, validated_data):
        items = validated_data.pop("items", None)
        validated_data.pop("user", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if items is not None:
            instance.items.all().delete()
            for it in items:
                OrderItem.objects.create(order=instance, **it)
        return instance
