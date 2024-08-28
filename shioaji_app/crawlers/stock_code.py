import json
import os
import requests

from io import StringIO
import pandas as pd

import shioaji as sj


def download():
    website_stock_codes = get_stock_codes_from_website()
    shioaji_stocks = get_stock_from_shioaji()
    stock_industry_mapping, industry_list = get_industry(shioaji_stocks, website_stock_codes)
    generate_industry_data(industry_list)
    generate_stock_code_data(shioaji_stocks, stock_industry_mapping)


def generate_stock_code_data(stocks, stock_industry_mapping):
    with open('', 'r', encoding='utf-8') as f:
        industry_data = json.load(f)


    industry_name_mapping = {}
    for industry in industry_data:
        industry_name = industry['fields']['name']
        pk = industry['pk']
        industry_name_mapping[industry_name] = pk
    output = []
    pk = 1
    for stock in stocks:
        code = stock['code']
        if code not in stock_industry_mapping:
            continue
        industry_name = stock_industry_mapping[code]
        industry_pk = industry_name_mapping[industry_name]
        data = {
            'model': 'shioaji_app.stock',
            'pk': pk,
            'fields': {
                'name': stock['name'],
                'code': code,
                'exchange': stock['exchange'],
                'industries': [industry_pk],
            }
        }
        output.append(data)
        pk += 1
    with open('./shioaji_app/fixtures/stock_code/data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False)

def generate_industry_data(industry_list):
    output = []
    pk = 1
    for industry in industry_list.values():
        data = {
            'model': 'shioaji_app.industry',
            'pk': pk,
            'fields': {
                'name': industry
            }
        }
        output.append(data)
        pk += 1
    with open('./shioaji_app/fixtures/industry/data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False)

def get_industry(stocks, industry_data):
    industry_table = industry_data.set_index('code')
    industry_mapping = {}
    industry_list = {}
    for stock in stocks:
        code = stock['code']
        category = stock['category']
        if code not in industry_table.index:
            continue
        industry = industry_table.loc[code].industry
        if category not in industry_list:
            industry_mapping[code] = industry
            industry_list[category] = industry
        elif industry_list[category] != industry:
            print(code, '資料不一致')
        industry_mapping[code] = industry
    return industry_mapping, industry_list

def get_stock_from_shioaji():
    api = sj.Shioaji()
    api_key = os.getenv('SHIOAJI_API_KEY')
    secret_key = os.getenv('SHIOAJI_SECRET_KEY')
    api.login(
        api_key=api_key,
        secret_key=secret_key,
        contracts_cb=lambda security_type: print(f"{repr(security_type)} fetch done.")
    )

    tse_stocks = [s for s in api.Contracts.Stocks.TSE if len(s.code) == 4]
    otc_stocks = [s for s in api.Contracts.Stocks.OTC if len(s.code) == 4]
    stocks = tse_stocks + otc_stocks

    return stocks

def get_stock_codes_from_website():

    tse_df = get_data_from_isin()
    otc_df = get_data_from_isin(market='OTC')
    df = pd.concat([tse_df, otc_df])

    return df


def get_data_from_isin(market='TSE'):
    TSE_CODE = 2
    OTC_CODE = 4
    url = None
    if market == 'TSE':
        url = f'https://isin.twse.com.tw/isin/C_public.jsp?strMode={TSE_CODE}'
    if market == 'OTC':
        url = f'https://isin.twse.com.tw/isin/C_public.jsp?strMode={OTC_CODE}'

    if url is None:
        raise Exception('The market has not been supported.')

    encoding = 'big5'
    res = requests.get(url)
    res.encoding = encoding

    # 直接讀網頁會導致資料不完整-.-凸 所以外面包一層StringIO
    dfs = pd.read_html(StringIO(res.text))


    df = dfs[0][[0, 4]].dropna()
    df['split_text'] = df[0].str.split('\u3000')

    df = df[df['split_text'].str.len() == 2]
    df[['code', 'name']] = df['split_text'].apply(lambda x: pd.Series(x[:2]))
    del df['split_text']
    del df[0]

    df.columns = ['industry', 'code', 'name']


    return df


if __name__ == '__main__':
    download()