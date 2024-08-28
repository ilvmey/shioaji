# 三大法人買賣超
from datetime import datetime
import requests

from io import StringIO
import pandas as pd
import django
django.setup()
from shioaji_app.models import Institution, Stock



def download():
    trade_date = datetime(2023, 5, 31)
    trade_date_str = trade_date.strftime('%Y%m%d')
    url = f'https://www.twse.com.tw/rwd/zh/fund/T86?date={trade_date_str}&selectType=ALLBUT0999&response=csv'
    res = requests.get(url)
    df = pd.read_csv(StringIO(res.text), header=1).dropna(how='all', axis=1).dropna(how='any')
    df = df.astype(str).apply(lambda s: s.str.replace(',',''))
    df['證券代號'] = df['證券代號'].str.replace('=','').str.replace('"','')

    for _, row in df.iterrows():
        code = row['證券代號']
        result = Stock.objects.filter(code=code)
        if result.exists():
            stock = result.first()  # 取得第一個符合條件的物件
        else:
            continue


        foreign_buy_shares = float(row['外陸資買進股數(不含外資自營商)']) + float(row['外資自營商買進股數']) + float(row['外資自營商買進股數'])
        shares = int(foreign_buy_shares)
        create_institution_record(shares, 'buy', 'foreign', trade_date, stock)

        foreign_sell_shares = float(row['外陸資賣出股數(不含外資自營商)']) + float(row['外資自營商賣出股數']) + float(row['外資自營商賣出股數'])
        shares = int(foreign_sell_shares)
        create_institution_record(shares, 'sell', 'foreign', trade_date, stock)

        net_shares = float(row['外陸資買賣超股數(不含外資自營商)']) + float(row['外資自營商買賣超股數'])
        shares = int(net_shares)
        create_institution_record(shares, 'net', 'foreign', trade_date, stock)

        investment_trust_buy_shares = row['投信買進股數']
        shares = int(float(investment_trust_buy_shares))
        create_institution_record(shares, 'buy', 'investment_trust', trade_date, stock)

        investment_trust_sell_shares = row['投信賣出股數']
        shares = int(float(investment_trust_sell_shares))
        create_institution_record(shares, 'sell', 'investment_trust', trade_date, stock)

        investment_trust_net_shares = row['投信買賣超股數']
        shares = int(float(investment_trust_net_shares))
        create_institution_record(shares, 'net', 'investment_trust', trade_date, stock)


def create_institution_record(shares, trade_type, institution_type, trade_date, stock):
        institution = Institution()
        institution.trade_type = trade_type
        institution.institution_type = institution_type
        institution.shares = int(float(shares))
        institution.trade_date = trade_date
        institution.stock = stock

        institution.save()

if __name__ == "__main__":
    download()