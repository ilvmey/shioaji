from django.db import models

class Stock(models.Model):
    code = models.CharField(max_length=4, null=True)
    name = models.CharField(max_length=25, null=True)
    exchange = models.CharField(max_length=3, null=True)
    industries = models.ManyToManyField('Industry')


class Industry(models.Model):
    name = models.CharField(max_length=10)

class Institution(models.Model):
    TRADE_TYPE_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
        ('net', 'Net'),
    ]

    trade_type = models.CharField(max_length=4, choices=TRADE_TYPE_CHOICES)

    INSTITUTION_TYPE_CHOICES = [
        ('foreign', '外資'),
        ('investment_trust', '投信'),
        ('proprietary', '自營'),
    ]
    institution_type = models.CharField(max_length=20, choices=INSTITUTION_TYPE_CHOICES)
    shares = models.IntegerField(default=0)
    trade_date = models.DateField()
    stock = models.ForeignKey(Stock,
                                on_delete=models.CASCADE,
                                null=True,
                                related_name='institutions')


class KBar(models.Model):
    open = models.DecimalField(max_digits=10, decimal_places=2)
    high = models.DecimalField(max_digits=10, decimal_places=2)
    low = models.DecimalField(max_digits=10, decimal_places=2)
    close = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.DecimalField(max_digits=20, decimal_places=2)
    timestamp = models.DateTimeField()

    stock = models.ForeignKey(Stock,
                                on_delete=models.CASCADE,
                                null=True,
                                related_name='kbars')