from django.db import models

class VPNUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=100, null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=50, null=True, blank=True)  # Optional for future
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username or str(self.telegram_id)


class SubscriptionPlan(models.Model):
    DURATION_CHOICES = [
        ('1m', '1 ماهه'),
        ('3m', '3 ماهه'),
        ('6m', '6 ماهه'),
        ('12m', '12 ماهه'),
    ]
    duration_code = models.CharField(max_length=10, choices=DURATION_CHOICES)
    label = models.CharField(max_length=50)  # فارسی label to show to user

    def __str__(self):
        return self.label

class VPNShowcaseConfig(models.Model):
    TYPE_CHOICES = [
        ('volume', 'حجمی'),
        ('unlimited', 'نامحدود'),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    bandwidth_gb = models.IntegerField(null=True, blank=True)
    price_toman = models.IntegerField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} - {self.price_toman} تومان"


class VPNConfig(models.Model):
    TYPE_CHOICES = [
        ('volume', 'حجمی'),
        ('unlimited', 'نامحدود'),
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)  # e.g. "200 گیگ سه کاربره"
    bandwidth_gb = models.IntegerField(null=True, blank=True)  # Add this field
    price_toman = models.IntegerField()
    active = models.BooleanField(default=True)
    config_text = models.TextField(null=True,blank=True)

    def __str__(self):
        return f"{self.title} - {self.price_toman} تومان"

class VPNDelivery(models.Model):
    user = models.ForeignKey('VPNUser', on_delete=models.CASCADE)
    config = models.ForeignKey('VPNConfig', on_delete=models.CASCADE)
    delivered_at = models.DateTimeField(auto_now_add=True)
    manually_sent = models.BooleanField(default=True)  # sent via /sendvpn or future auto-delivery
    def __str__(self):
        return f"{self.user.username} ← {self.config.title} at {self.delivered_at}"


class PaymentSettings(models.Model):
    admin_user_id = models.BigIntegerField(default=0)  # Telegram numeric ID of admin
    card_number = models.CharField(max_length=30)      # e.g. 6129888888888888
    card_holder_name = models.CharField(max_length=100)  # e.g. املاکی دلقک
    active = models.BooleanField(default=True)          # Allow toggling between multiple configs if needed

    class Meta:
        verbose_name = "Payment Setting"
        verbose_name_plural = "Payment Settings"

    def __str__(self):
        return f"{self.card_holder_name} - {self.card_number}"