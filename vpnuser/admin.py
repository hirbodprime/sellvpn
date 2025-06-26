from django.contrib import admin
from .models import VPNConfig, VPNUser, SubscriptionPlan, PaymentSettings,VPNDelivery


admin.site.register(VPNDelivery)
admin.site.register(VPNUser)
admin.site.register(VPNConfig)
admin.site.register(SubscriptionPlan)
admin.site.register(PaymentSettings)