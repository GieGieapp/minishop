from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id","name","sku","price","stock","is_active","created_at","updated_at"]
        read_only_fields = ["id","created_at","updated_at"]

    def validate(self, attrs):
        # contoh validasi bisnis ringan
        if attrs.get("price", 0) == 0 and attrs.get("is_active", True):
            raise serializers.ValidationError("Produk aktif tidak boleh berharga 0.")
        return attrs
