from django.db import models
from django.core.validators import MinValueValidator

# --- Choices ---

class ResourceType(models.TextChoices):
    FUEL = 'FUEL', 'Паливо'
    GOODS = 'GOODS', 'Товари'
    SUPPLIES = 'SUPPLIES', 'Витратні матеріали'

class PriorityLevel(models.IntegerChoices):
    NORMAL = 1, 'Нормальний'
    HIGH = 2, 'Підвищений'
    CRITICAL = 3, 'Критичний'

class RequestStatus(models.TextChoices):
    PENDING = 'PENDING', 'Очікує'
    PARTIAL = 'PARTIAL', 'Частково розподілено'
    ALLOCATED = 'ALLOCATED', 'Розподілено'
    SHIPPED = 'SHIPPED', 'Відправлено'
    COMPLETED = 'COMPLETED', 'Доставлено'
    CANCELLED = 'CANCELLED', 'Скасовано'


class TransactionType(models.TextChoices):
    ALLOCATION = 'ALLOCATION', 'Виділення зі складу'
    PREEMPT_OUT = 'PREEMPT_OUT', 'Списання на перерозподіл'
    PREEMPT_IN = 'PREEMPT_IN', 'Отримання через перерозподіл'
    SHORTAGE = 'SHORTAGE', 'Нестача ресурсу'

# --- Base ---

class BaseLocation(models.Model):
    name = models.CharField(max_length=255, verbose_name="Назва об'єкта")
    city = models.CharField(max_length=100, db_index=True, verbose_name="Місто")
    # Додали дефолт 0.0, щоб Django не панікував
    latitude = models.FloatField(default=0.0, verbose_name="Широта")
    longitude = models.FloatField(default=0.0, verbose_name="Довгота")

    class Meta:
        abstract = True

# --- Entities ---

class Warehouse(BaseLocation):
    def __str__(self):
        return f"Склад: {self.name} ({self.city})"

class Stock(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stocks')
    resource_type = models.CharField(max_length=20, choices=ResourceType.choices)
    
    actual_quantity = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0)], 
        verbose_name="Фактична кількість"
    )
    reserved_quantity = models.FloatField(
        default=0.0, 
        validators=[MinValueValidator(0.0)],
        verbose_name="Зарезервовано"
    )

    class Meta:
        unique_together = ('warehouse', 'resource_type')

    @property
    def available_quantity(self):
        return self.actual_quantity - self.reserved_quantity

class DeliveryPoint(BaseLocation):
    def __str__(self):
        return f"Точка: {self.name} ({self.city})"

class Request(models.Model):
    point = models.ForeignKey(DeliveryPoint, on_delete=models.CASCADE, related_name='requests')
    resource_type = models.CharField(max_length=20, choices=ResourceType.choices)
    
    quantity_requested = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)])
    quantity_allocated = models.FloatField(default=0.0)
    
    priority = models.IntegerField(
        choices=PriorityLevel.choices, 
        default=PriorityLevel.NORMAL,
        db_index=True
    )
    is_urgent = models.BooleanField(default=False, verbose_name="Терміновий запит")
    status = models.CharField(
        max_length=20, 
        choices=RequestStatus.choices, 
        default=RequestStatus.PENDING
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_status(self):
        if self.quantity_allocated >= self.quantity_requested:
            self.status = RequestStatus.ALLOCATED
        elif self.quantity_allocated > 0:
            self.status = RequestStatus.PARTIAL
        else:
            self.status = RequestStatus.PENDING

    class Meta:
        ordering = ['-priority', '-is_urgent', '-created_at']

# --- Logs ---

class AllocationHistory(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='history')
    old_quantity = models.FloatField(default=0.0)
    new_quantity = models.FloatField(default=0.0)
    reason = models.TextField(default="Зміна попиту", verbose_name="Причина")
    change_date = models.DateTimeField(auto_now_add=True)

class Shipment(models.Model):
    request = models.OneToOneField(Request, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True)
    estimated_arrival = models.DateTimeField(null=True, blank=True)
    tracking_number = models.CharField(max_length=50, unique=True, null=True, blank=True)


class ResourceTransaction(models.Model):
    request = models.ForeignKey(Request, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    resource_type = models.CharField(max_length=20, choices=ResourceType.choices)
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    quantity = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)])
    from_location = models.CharField(max_length=255, blank=True, default='')
    to_location = models.CharField(max_length=255, blank=True, default='')
    note = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']