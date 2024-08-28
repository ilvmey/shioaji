from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
import django

from shioaji_app.kbar_processor import DownloadKBarProducer, handle_kbar

django.setup()
import pandas as pd

# from stock.settings import api
# do not use relative path, eg: from models import Stock
from shioaji_app.models import Industry, Stock



if __name__ == '__main__':
    import os
    import shioaji as sj
    from shioaji_app.kbar_processor import conn, download_kbar_queue

    # financial_industry = Industry.objects.get(name='金融保險業')
    # semiconductor_industry = Industry.objects.get(name='半導體業')
    # target_industries = [financial_industry, semiconductor_industry]
    # stocks = Stock.objects.filter(industries__in=target_industries).all().order_by('code')
    stocks = Stock.objects.all().order_by('code')
    producer = DownloadKBarProducer(conn, download_kbar_queue)

    api = sj.Shioaji()
    api_key = os.getenv('SHIOAJI_API_KEY')
    secret_key = os.getenv('SHIOAJI_SECRET_KEY')
    api.login(
        api_key=api_key,
        secret_key=secret_key,
        contracts_cb=lambda security_type: print(f"{repr(security_type)} fetch done.")
    )

    start_date = (datetime.today() - relativedelta(years=1)).date().strftime('%Y-%m-%d')

    for stock in stocks:
        producer.send({'start_date': start_date, 'stock_code': stock.code, 'stock_id': stock.id})
        # df = handle_kbar(df)
        # break

