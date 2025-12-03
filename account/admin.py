from django.contrib import admin
from .models import customers,vendor,Account,Journal,JournalEntry,JournalItems,customer_contact,product,salesInvoice,InvoiceLine,vendor_product,purchaseinvoice,purchaseInvoiceLine,customer_payment,vendor_payment
# Register your models here.
admin.site.register(Account)

class AccountAdmin(admin.ModelAdmin):
    exclude =('code',)


admin.site.register(customers)
admin.site.register(customer_contact)
admin.site.register(product)
admin.site.register(salesInvoice)


admin.site.register(InvoiceLine)
admin.site.register(customer_payment)

admin.site.register(Journal)
class journalAdmin(admin.ModelAdmin):
    exclude =('code',)

admin.site.register(JournalEntry)
class journalentryAdmin(admin.ModelAdmin):
    exclude =('reference',)

admin.site.register(JournalItems)

admin.site.register(vendor)
admin.site.register(vendor_product)
admin.site.register(purchaseinvoice)
admin.site.register(purchaseInvoiceLine)
admin.site.register(vendor_payment)


