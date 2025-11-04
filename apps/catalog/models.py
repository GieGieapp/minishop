from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=160)
    sku = models.CharField(max_length=64, unique=True, db_index=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(check=models.Q(price__gte=0), name="product_price_gte_0"),
            models.CheckConstraint(check=models.Q(stock__gte=0), name="product_stock_gte_0"),
        ]

    def __str__(self):
        return f"{self.sku} - {self.name}"
