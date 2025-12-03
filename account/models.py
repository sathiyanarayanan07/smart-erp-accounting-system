from django.db import models
from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from django.db.models.signals import post_save,post_delete
from django.dispatch import receiver

# Create your models here.


class AccountType(models.TextChoices):
    ASSET ="asset","asset"
    LIABILITY ="liability","liability"
    EQUITY ="equity","equity"
    INCOME ="income","income"
    EXPENSE ="expense","expense"


class Account(models.Model):
    code = models.CharField(max_length=20, unique=True, blank=True)
    name =models.CharField(max_length=255,null=True,blank=True)
    account_Type =models.CharField(max_length=20,choices=AccountType.choices)
    category = models.CharField(max_length=255)
    parent =models.ForeignKey('self',on_delete=models.CASCADE,null=True,blank=True)
    balance = models.DecimalField(max_digits=15,decimal_places=2,default=0)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
            return f"{self.id}-{self.code} - {self.name}-{self.category}"
    
    def save(self,*args,**kwargs):
        if not self.code:
            first_account = Account.objects.order_by("-id").first()
            if first_account and first_account.code.isdigit():
                next_code =int(first_account.code)+ 1
                self.code = str(next_code).zfill(4)
            else:
                self.code ="1000"
        super().save(*args, **kwargs)           


class JournalType(models.TextChoices):
      SALES ="Sales","Sales"
      PURCHASES="Purchases","Purchases"
      CASH ="Cash","Cash"
      BANK= "Bank","Bank"
      MISCELLANEOUS ="Miscellaneous","Miscellaneous"
      GENERAL ="General","General"
      PAYROLL ="Payroll","Payroll"
      TAX="Tax","Tax"



class Journal(models.Model):
    code = models.CharField(max_length=20,unique=True,blank=True)
    journal_name =models.CharField(max_length=100,blank=True,null=True)
    type =models.CharField(max_length=20,choices=JournalType.choices)
    description = models.TextField(blank=True,null=True)

    def __str__(self):
        return f"{self.code}-{self.journal_name}--{self.id}"
    
    def save(self, *args,**kwargs):
        if not self.code:
            journal_code = Journal.objects.order_by("-id").first()
            if journal_code and journal_code.code.isdigit():
                next_code =int(journal_code.code)+1
                self.code = str(next_code).zfill(4)
            else:
                self.code ="1001"    
        super().save(*args,**kwargs)


class JournalEntryStatus(models.TextChoices):
    POSTED = "posted", "posted"
    DRAFT = "Draft", "Draft"             

class JournalEntry(models.Model):
    reference = models.CharField(max_length=50, blank=True, null=True)
    accounting_date = models.DateField(default=timezone.now)
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=JournalEntryStatus.choices, default="Draft")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.journal.journal_name

    def total_debits(self):
        return self.items.aggregate(total=models.Sum('debit'))['total'] or Decimal("0.00")

    def total_credits(self):
        return self.items.aggregate(total=models.Sum('credit'))['total'] or Decimal("0.00")

    def is_balanced(self):
        return self.total_debits() == self.total_credits()

    def post(self):
        if self.status == "posted":
            return
        if not self.is_balanced():
            raise ValueError("Journal Entry is not balanced")

        for item in self.items.all():
            if item.debit and item.debit > 0:
                item.account.balance += item.debit
            if item.credit and item.credit > 0:
                item.account.balance -= item.credit
            item.account.save()

        self.status =JournalEntryStatus.POSTED
        self.save()
       
    def save(self, *args,**kwargs):
        if not self.reference:
            journalentry_reference = JournalEntry.objects.order_by("-id").first()
            if journalentry_reference and journalentry_reference.reference.isdigit():
                next_code =int(journalentry_reference.reference)+1
                self.reference = str(next_code).zfill(6)
            else:
                self.reference ="10011"   
        super().save(*args,**kwargs)



    
class JournalItems(models.Model):
    account =models.ForeignKey(Account,on_delete=models.CASCADE)
    journalentry =models.ForeignKey(JournalEntry,on_delete=models.CASCADE,related_name='items')
    partner = models.CharField(max_length=100,null=True,blank=True)
    label = models.CharField(max_length=255,blank=True,null=True)
    debit =models.DecimalField(max_digits=15,decimal_places=2,null=True,blank=True)
    credit =models.DecimalField(max_digits=15,decimal_places=2,null=True,blank=True)

    def __str__(self):
        return self.account.name


from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


# -------------------------
# SIGNALS TO UPDATE BALANCE
# -------------------------
def update_account_balance(account):
    """Recalculate account balance based on all journal items"""
    total_debit = JournalItems.objects.filter(account=account).aggregate(Sum("debit"))["debit__sum"] or 0
    total_credit = JournalItems.objects.filter(account=account).aggregate(Sum("credit"))["credit__sum"] or 0
    account.balance = total_debit - total_credit
    account.save()


@receiver(post_save, sender=JournalItems)
def update_balance_on_save(sender, instance, **kwargs):
    update_account_balance(instance.account)


@receiver(post_delete, sender=JournalItems)
def update_balance_on_delete(sender, instance, **kwargs):
    update_account_balance(instance.account)



class CustomerStatus(models.TextChoices):
    active ="active","active"
    inactive ="inactive","inactive"
    suspended ="suspended","suspended"



class customers(models.Model):
    name = models.CharField(max_length=100,null=True,blank=True)
    email = models.EmailField(max_length=100,null=True,blank=True)
    phone = models.CharField(max_length=100,null=True,blank=True)
    address =models.TextField(max_length=100,blank=True,null=True)
    City = models.CharField(max_length=20,blank=True,null=True)
    state = models.CharField(max_length=20,blank=True,null=True)
    Country = models.CharField(max_length=20,null=True,blank=True)
    Zip_code= models.CharField(max_length=255,null=True,blank=True)
    status = models.CharField(max_length=100,choices=CustomerStatus.choices,default=CustomerStatus.active)
    gstin = models.CharField(max_length=100,null=True,blank=True)
    pan = models.CharField(max_length=100,null=True,blank=True)
    tax_id = models.CharField(max_length=100,blank=True,null=True)
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField()
    website= models.URLField(max_length=100,null=True,blank=True)

    def __str__(self):
        return f"{self.name}-{self.id}"
    
    
    
class customer_contact(models.Model):
    name =models.CharField(max_length=100,null=True,blank=True)
    email =models.CharField(max_length=100,null=True,blank=True)
    phone = models.CharField(max_length=10,null=True,blank=True)
    job_title =models.CharField(max_length=30,null=True,blank=True)
    notes= models.TextField()

    def __str__(self):
        return f"{self.name}--{self.email}"
    
class producttype(models.TextChoices):
    goods ="GOODS","GOODS"
    service ="service","service"
    combo ="combo","combo"
    
class product(models.Model):
    Name = models.CharField(max_length=255,blank=True,null=True)
    sales = models.BooleanField(default='False')
    purchase =models.BooleanField(default='false')
    product_type = models.CharField(max_length=20,choices=producttype.choices)
    price =models.DecimalField(max_digits=10,decimal_places=2)
    description = models.TextField()

    def __str__(self):
        return f"{self.id}-{self.Name}"

class PaymentTerms(models.TextChoices):
    payment ="Immediate payment","Immediate payment"
    Days= "15 Days","15 Days"
    twenty="20 Days","20 Days"
    thirty ="30 Days", "30 Days"
    fourty ="45 Days","45 Days"
    month = " End of following Month","End of following Month"

class InvoiceStatus(models.TextChoices):
    POSTED="posted","posted"
    DRAFT="draft","draft" 
    PAID="paid","paid"
    CANCELLED ="cancelled","cancelled"   


class salesInvoice(models.Model):
    customer = models.ForeignKey(customers, on_delete=models.CASCADE)
    invoice_Date = models.DateField(default=timezone.now)
    Due_Date = models.DateField(null=True, blank=True)
    payments_terms = models.CharField(max_length=30, choices=PaymentTerms.choices)
    Status = models.CharField(max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.DRAFT)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    journals = models.ForeignKey(Journal, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id}--{self.customer.name}"
    
    def calculate_total(self):
        self.total = sum([line.quantity * line.price for line in self.lines.all()])
        self.save()

    def post(self):
        if self.Status != InvoiceStatus.DRAFT:
            return  

        # create journal entry
        je = JournalEntry.objects.create(
            journal_id=self.journals.id if self.journals else None,
            description=f"Invoice{self.id} - {self.customer}",
            status=JournalEntryStatus.DRAFT
        )

        # Accounts Receivable
        receivable = Account.objects.get(code="1000")
        JournalItems.objects.create(
            account=receivable,
            journalentry=je,
            partner=self.customer.name,
            label=f"Invoice {self.id}",
            debit=self.total,
            credit=Decimal("0.00")
        )

        # Sales Revenue
        sales = Account.objects.get(code="4000")
        JournalItems.objects.create(
            account=sales,
            journalentry=je,
            partner=self.customer.name,
            label=f"Invoice {self.id}",
            debit=Decimal("0.00"),
            credit=self.total
        )

        # Post JE
        je.post()

        # Update invoice + customer balance
        self.Status = InvoiceStatus.POSTED
        self.save()

        self.customer.current_balance = (self.customer.current_balance or Decimal("0.00")) + self.total
        self.customer.save()

        return je


    
       

    

class InvoiceLine(models.Model):
    invoices= models.ForeignKey(salesInvoice,on_delete=models.CASCADE,related_name="lines",null=True,blank=True)
    Product = models.ForeignKey(product,on_delete=models.CASCADE,null=True,blank=True)
    Accounts = models.ForeignKey(Account,on_delete=models.CASCADE,null=True,blank=True)
    quantity = models.DecimalField(max_digits=12,decimal_places=2)
    price = models.DecimalField(max_digits=12,decimal_places=2)
    description = models.TextField(null=True,blank=True)
    notes = models.TextField(null=True,blank=True)

    def __str__(self):
        return f"{self.Product}-{self.price}"


@receiver(post_save,sender=InvoiceLine) 
@receiver(post_delete, sender=InvoiceLine)
def update_invoice_total(sender, instance, **Kwargs):
    instance.invoices.calculate_total()

class paymentstatus(models.TextChoices):
    PAID ="paid","paid"
    DRAFT ="draft","draft"


class customer_payment(models.Model):
    customer =models.ForeignKey(customers,on_delete=models.CASCADE)
    invoice =models.ForeignKey(salesInvoice,on_delete=models.CASCADE)
    payment_date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=15,decimal_places=2,default=0)
    journal = models.ForeignKey(Journal,on_delete=models.CASCADE)
    reference = models.CharField(max_length=255,blank=True,null=True)
    status =models.CharField(max_length=20,choices=paymentstatus.choices)

    def __str__(self):
        return f"payment{self.id}--{self.amount}"
    
    def post(self):
        if self.status != paymentstatus.DRAFT:
            return
        
        #create journal entry
        jep= JournalEntry.objects.create(
            journal_id =self.journal.id if self.journal else None,
            description =f"payment {self.id} - {self.customer}",
            status =JournalEntryStatus.DRAFT
        )

        back_cash =Account.objects.get(code="1200")
        JournalItems.objects.create(
            account =back_cash,
            journalentry=jep,
            partner =self.customer.name,
            label = f"payment{self.id}",
            debit=self.amount,
            credit= Decimal("0.00")
            )
        
        receivable= Account.objects.get(code='1000')
        JournalItems.objects.create(
            account =receivable,
            journalentry=jep,
            partner =self.customer.name,
            label=f"payment{self.id}",
            debit=Decimal('0.00'),
            credit=self.amount


        )

        jep.post()

        #update invoice +customer balance
        self.status = paymentstatus.PAID
        self.save()

        self.customer.current_balance =(self.customer.current_balance or Decimal("0.00"))-self.amount
        self.customer.save()

        return jep



    

  
class vendor(models.Model):
    name = models.CharField(max_length=100,blank=True,null=True)
    Company_name =models.CharField(max_length=100,blank=True,null=True)
    email = models.EmailField(max_length=100,null=True,blank=True)
    phone = models.CharField(max_length=100,null=True,blank=True)
    Category = models.CharField(max_length=100,null=True,blank=True)
    address = models.TextField()
    city = models.CharField(max_length=20,blank=True,null=True)
    state = models.CharField(max_length=20,blank=True,null=True)
    zipcode =models.CharField(max_length=20,blank=True,null=True)
    country = models.CharField(max_length=20,blank=True,null=True)
    tax_id = models.CharField(max_length=100,blank=True,null=True)
    payment =models.IntegerField(default=30)
    current_balance =models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField()
    notes = models.TextField()

    def __str__(self):
        return f"{self.id}-{self.name}"


class vendor_producttype(models.TextChoices):
    goods ="GOODS","GOODS"
    service ="service","service"
    combo ="combo","combo"
    
class vendor_product(models.Model):
    Name = models.CharField(max_length=255,blank=True,null=True)
    sales = models.BooleanField(default='False')
    purchase =models.BooleanField(default='false')
    product_type = models.CharField(max_length=20,choices=producttype.choices)
    price =models.DecimalField(max_digits=10,decimal_places=2)
    description = models.TextField()

    def __str__(self):
        return f"{self.id}-{self.Name}"

class PaymentTerms(models.TextChoices):
    payment ="Immediate payment","Immediate payment"
    Days= "15 Days","15 Days"
    twenty="20 Days","20 Days"
    thirty ="30 Days", "30 Days"
    fourty ="45 Days","45 Days"
    month = " End of following Month","End of following Month"

class purchaseInvoiceStatus(models.TextChoices):
    POSTED="posted","posted"
    DRAFT="draft","draft" 
    PAID="paid","paid"
    CANCELLED ="cancelled","cancelled"   

    
class purchaseinvoice(models.Model):
    vendor = models.ForeignKey(vendor,on_delete=models.CASCADE)
    invoice_Date = models.DateField(default=timezone.now)
    Due_Date = models.DateField(null=True, blank=True)
    payments_terms = models.CharField(max_length=30, choices=PaymentTerms.choices)
    Status = models.CharField(max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.DRAFT)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    journals = models.ForeignKey(Journal, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id}-{self.vendor.name}"
    

    def calculate_total_vendor(self):
        self.total = sum([vendors.quantity * vendors.price for vendors in self.lines.all()])
        self.save()

    def post(self):
        if self.Status != purchaseInvoiceStatus.DRAFT:
            return
        
        
        jev =JournalEntry.objects.create(
            journal_id =self.journals.id if self.journals  else None,
            description =f"bill {self.id}-{self.vendor.name}",
            status=JournalEntryStatus.DRAFT
    )
        expense =Account.objects.get(code='5000')
        JournalItems.objects.create(
            account =expense,
            journalentry =jev,
            partner = self.vendor.name,
            label =f"bill {self.id}",
            debit =self.total,
            credit=Decimal("0.00")
        )

        ap=Account.objects.get(code="2000")
        JournalItems.objects.create(
            account=ap,
            journalentry=jev,
            partner=self.vendor.name,
            label=f"bill{self.id}",
            debit=Decimal("0.00"),
            credit=self.total

        )

        jev.post()


        #update invoice +vendor balance
        self.Status =purchaseInvoiceStatus.POSTED
        self.save()

        self.vendor.current_balance = (self.vendor.current_balance or Decimal("0.00"))+self.total
        self.vendor.save()

        return jev

        



class purchaseInvoiceLine(models.Model):
    invoices= models.ForeignKey(purchaseinvoice,on_delete=models.CASCADE,related_name="lines")
    products = models.ForeignKey(vendor_product,on_delete=models.CASCADE)
    accounts = models.ForeignKey(Account,on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12,decimal_places=2)
    price = models.DecimalField(max_digits=12,decimal_places=2)
    description = models.TextField(null=True,blank=True)
    notes = models.TextField(null=True,blank=True)

    def __str__(self):
        return f"{self.products}--{self.price}"
    
@receiver(post_save,sender=purchaseInvoiceLine)   
@receiver(post_delete,sender=purchaseInvoiceLine) 
def update_purchaseinvoe_total(sender, instance,**kwargs):
    instance.invoices.calculate_total_vendor()


class vendorpaymentstatus(models.TextChoices):
    PAID="paid","paid"
    DRAFT ="draft","draft"


class vendor_payment(models.Model):
    vendors =models.ForeignKey(vendor,on_delete=models.CASCADE,null=True,blank=True)
    invoice=models.ForeignKey(purchaseinvoice,on_delete=models.CASCADE,null=True,blank=True)
    payment_date =models.DateField(default=timezone.now)
    amount=models.DecimalField(max_digits=10,decimal_places=2,default=0)
    journal = models.ForeignKey(Journal,on_delete=models.CASCADE,null=True,blank=True)
    reference= models.CharField(max_length=255,blank=True,null=True)
    status =models.CharField(max_length=20,choices=vendorpaymentstatus.choices)

    def __str__(self):
        return f"bill{self.id}--{self.amount}"
    
    def post(self):
        if self.status != vendorpaymentstatus.DRAFT:
            return
        
        jeb =JournalEntry.objects.create(
            journal_id = self.journal.id if self.journal else None,
            description=f"bill {self.id}-{self.vendors}",
            status =JournalEntryStatus.DRAFT

        )

        bill = Account.objects.get(code='')
        JournalItems.objects.create(
            account =bill,
            journalentry =jeb,
            partner =self.vendors.name,
            label =f"bill{self.id}",
            debit =self.amount,
            credit=Decimal("0.00")
        )
        receivable= Account.objects.get(code='1000')
        JournalItems.objects.create(
            account =receivable,
            journalentry=jeb,
            partner =self.vendors.name,
            label=f"payment{self.id}",
            debit=Decimal('0.00'),
            credit=self.amount


        )

        jeb.post()

        #update invoice +customer balance
        self.status = vendorpaymentstatus.PAID
        self.save()

        self.customer.current_balance =(self.customer.current_balance or Decimal("0.00"))-self.amount
        self.customer.save()

        return jeb
