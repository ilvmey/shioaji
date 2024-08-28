import json
from decimal import Decimal
import os

import django

django.setup()

from kombu import Connection, Producer, Exchange, Queue
from kombu.mixins import ConsumerMixin, ConsumerProducerMixin
import pandas as pd
import talib

import shioaji as sj

from shioaji_app.models import Stock

# from stock.settings import api

exchange = Exchange('kbar', type='direct')
conn = Connection('amqp://stock:stock@localhost:5672//')
producer = Producer(conn)

kbar_queue = Queue(
    'kbar', exchange, routing_key='kbar')

download_kbar_queue = Queue(
    'download_kbar', exchange, routing_key='download_kbar_queue'
)

class KBarProducer(Producer):

    def send(self, message):

        self.publish(
            message,
            exchange=exchange,
            routing_key=kbar_queue.routing_key,
            # declares exchange, queue and binds.
            declare=[kbar_queue],
        )

class KBarConsumer(ConsumerMixin):

    def __init__(self, connection, queue_name):
        self.connection = connection
        self.queue_name = queue_name
        super().__init__()

    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=[kbar_queue], callbacks=[self.on_message], prefetch_count=1)]

    def on_message(self, body, message):
        data = json.loads(message.body)
        df = pd.DataFrame({**data})
        handle_kbar(df)
        message.ack()


class DownloadKBarProducer(Producer):

    def send(self, message):

        self.publish(
            message,
            exchange=exchange,
            routing_key=download_kbar_queue.routing_key,
            # declares exchange, queue and binds.
            declare=[download_kbar_queue],
        )

class DownloadKBarConsumer(ConsumerProducerMixin):

    def __init__(self, connection, queue_name):
        self.connection = connection
        self.queue_name = queue_name
        self.api = sj.Shioaji()
        api_key = os.getenv('SHIOAJI_API_KEY')
        secret_key = os.getenv('SHIOAJI_SECRET_KEY')
        self.api.login(
            api_key=api_key,
            secret_key=secret_key,
            contracts_cb=lambda security_type: print(f"{repr(security_type)} fetch done.")
        )
        super().__init__()

    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=[download_kbar_queue], callbacks=[self.on_message], prefetch_count=1)]

    def on_message(self, body, message):
        data = json.loads(message.body)
        stock_code = data['stock_code']
        stock_id = data['stock_id']
        start_date = data['start_date']
        # end_date = data.get('end_date')
        api = self.api
        kbars = api.kbars(
                            contract=api.Contracts.Stocks[stock_code],
                            start=start_date,
                            # start="2023-05-02",
        )

        df = pd.DataFrame({**kbars})
        df.ts = pd.to_datetime(df.ts)
        del df['Amount']
        df.rename(columns={'Close': 'close', 'High': 'high', 'Low': 'low', 'Open': 'open', 'Volume': 'volume', 'ts': 'timestamp'}, inplace=True)
        df['code'] = stock_code
        df['stock_id'] = stock_id

        self.producer.publish(df.to_json(date_format='iso'), exchange=exchange, routing_key=kbar_queue.routing_key)
        message.ack()


def custom_json_format(row):
    return {
        'model': 'shioaji_app.KBar',
        'fields': {
            'timestamp': row['datetime'],
            'open': row['open'],
            'high': row['high'],
            'low': row['low'],
            'close': row['close'],
            'volume': row['volume'],
            'stock': row['stock_id'],
        }
    }

def handle_kbar(df):
    if len(df) == 0:
        return
    df['datetime'] = pd.to_datetime(df['timestamp'])
    del df['timestamp']
    df['date'] = df['datetime'].dt.date
    code = df['code'][0]
    stock = Stock.objects.get(code=code)
    # 目前只有紀錄一個產業
    industry = [i for i in stock.industries.all()][0].name
    df_daily = df.groupby('date').agg({'open': 'first',
                                   'close': 'last',
                                   'high': 'max',
                                   'low': 'min',
                                   'volume': 'sum'})
    df_daily['stock_id'] = df['stock_id'][0]
    df_daily.reset_index(inplace=True)

    # df_daily.to_json(f'./shioaji_app/fixtures/{code}.json', date_format='iso', orient='records', force_ascii=False, default_handler=custom_json_format)
    # print(code)
    sma_20 = list(talib.SMA(df_daily['close'], 20))
    open_ = list(df_daily['open'])
    high = list(df_daily['high'])
    low = list(df_daily['low'])
    close = list(df_daily['close'])
    volume = list(df_daily['volume'])
    percentage_change = (Decimal(str(close[-1])) / Decimal(str(close[0])) - 1) * 100

    rounded = round(percentage_change, 3)

    with open('percentage_change.csv', 'a', encoding='utf-8') as f:
        f.write(f'{code},{industry},{rounded}\n')

    if sum(volume[-5:]) < 5000:
        return

    signal = []
    if sma_20[-1] > sma_20[-2] and sma_20[-2] < sma_20[-3]:
        signal.append('月均線轉上升')

    if sma_20[-1] > sma_20[-2] and sma_20[-2] > sma_20[-3]:
        signal.append('月均線上升')

    if not is_red_k(open_[-2] ,close[-2]) and is_red_k(open_[-1] ,close[-1]):
        if open_[-1] < close[-2] and close[-1] > open_[-2]:
            signal.append('多頭吞噬')

    if volume[-1] >= 2 * volume[-2]:
        signal.append('量增二倍')

    if signal:
        print(f"{code} {', '.join(signal)}")



def is_red_k(open, close):
    if open < close:
        return True
    if open > close:
        return False
    return False