from django.contrib import admin
from .models import VPNConfig, VPNUser, SubscriptionPlan, PaymentSettings,VPNDelivery,VPNShowcaseConfig

@admin.register(VPNShowcaseConfig)
class VPNShowcaseConfigAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "subscription_plan", "bandwidth_gb", "price_toman", "active")
    list_filter = ("type", "active")

admin.site.register(VPNDelivery)
admin.site.register(VPNUser)
admin.site.register(VPNConfig)
admin.site.register(SubscriptionPlan)
admin.site.register(PaymentSettings)