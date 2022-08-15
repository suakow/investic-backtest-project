import streamlit as st
import plotly.io as pio

import pandas as pd
import pandas_ta as ta
import numpy as np
import yfinance as yf
import vectorbt as vbt
import datetime

import mplfinance as mpf

st.set_option('deprecation.showPyplotGlobalUse', False)

st.title('Investic Event by Puri(suakow)')

"""
สวัสดีครับ มือใหม่มากๆ หลังจบกิจกรรมอยากให้คอมเมนท์รวมถึงแนะนำการใช้งาน Indicator เพิ่มเติมด้วยครับ ขอบคุณครับ

## Asset ที่เลือก
- BTC-USD (จาก Yahoo Finance)
- Timeframe : 1D
- 2021-01-01 to 2022-04-30 

เลือกช่วงนี้เพราะว่าเป็นช่วงที่ BTC มีทั้งขาขึ้นและขาลงครบ
"""

# Load Data
price_df = pd.read_pickle('data/btcusd_20210101_20220430.bin')
st.dataframe(data=price_df)

"""
## Indicators
เนื่องจากมี Idea ที่ว่า ต้องการให้ Trade โดยที่ราคาเป็น Trend และ Sideway ได้ จึงเลือกใช้ Indicator ทั้งในรูปแบบ Trend following และ Oscillator 
- EMA(15)
- MACD(Default)
"""

#Add Indicators
df = price_df.copy()
df.ta.ema(15, append=True)
df.ta.macd(append=True)

st.dataframe(data=df.tail())

"""
จากนั้น นำ Indicator และกราฟแท่งเทียนมา Plot รวมกันได้ดังรูปนี้
"""

all_plot = [ 
            mpf.make_addplot(df['EMA_15'], panel=0, color='orange'),
            mpf.make_addplot(df['MACDh_12_26_9'], panel=1, color='orange'),
            ]

df.index = pd.to_datetime(df.index)

price_plot = mpf.plot(df, type='candle', style='yahoo', addplot=all_plot, figsize=(20, 15))
st.pyplot(price_plot)

"""
## Strategy

การกำหนดการซื้อขายจะทำดังนี้
- ซื้อขายทางเดียว (Long only)
- จะซื้อเมื่อราคาปิดของวันก่อนหน้า 1 วันมากกว่า EMA 15 "หรือ" MACD Histogram > 0

เมื่อเขียนเป็น Function จะได้ Code ดังนี้
"""

st.code("""
df['signal_buy'] = df.apply(lambda _ : ((_['Close'] > _['EMA_15']) or (_['MACDh_12_26_9'] > 0)),
                            axis=1)""")

df['signal_buy'] = df.apply(lambda _ : ((_['Close'] > _['EMA_15']) or (_['MACDh_12_26_9'] > 0)),
                            axis=1)

buy_signal_df = df.ta.tsignals(df['signal_buy'], asbool=True, append=True)
buy_signal_df['TS_Entries'] = buy_signal_df['TS_Entries'].shift(1).fillna(False)

"""
## Backtesting

ในการ Backtest กำหนด Parameters ดังนี้
- Initial cash = 100,000
- Stoploss = 5%
- Fee = 0.25%
- Slippage = 0.25%

โดย Shift 1 วัน แล้วทำการคำนวณ Backtest ด้วยราคาเปิด

ได้ผลการ Backtest ดังนี้
"""
port = vbt.Portfolio.from_signals(df['Open'],
                                 entries=buy_signal_df['TS_Entries'], # Long Entry
                                 exits=buy_signal_df['TS_Exits'], # Long Exit
                                 freq='D',
                                 init_cash=100_000,
                                 sl_stop=0.05,
                                 fees=0.0025,
                                 slippage=0.0025)

port_stats = port.stats()

st.code(port_stats)

st.plotly_chart(port.plot())


"""
## วิเคราห์ผล

- สังเกตว่า False Signal มีเยอะมาก โดยเฉพาะช่วง Sideway เคยพยายามแก้ Sideway ด้วย Bollinger Bands โดยใช้ความกว้างของ Band เป็นเกณฑ์ เพราะสังเกตว่าหาก Band แคบจะเป็นช่วง Sideway แต่ก็ไม่สำเร็จ (ไม่ใช้ได้ผลดีกว่า) จึงอยากได้คำชี้แนะว่าควรใช้ Indicators อะไรดี หรืออยากให้ศึกษาอะไรเพิ่มเติม
- แต่เนื่องจาก False Signal เยอะมาก จึงกำหนด Stoploss ที่ค่อนข้างต่ำเพื่อลดผล False Signal -> ตรงนี้ได้ผลที่ดีขี้น

### ข้อดี
- ระบบเข้าใจได้ง่าย ไม่ซับซ้อนเลย
- ช่วงที่ Trend ชัดเจนสามารถได้กำไรสูงได้
- ได้กำไรในช่วง Sideway ได้บางครั้ง 

### ข้อเสีย
- False signal เยอะมากกกกก แต่พอแก้ได้ด้วยการกำหนด Stoploss 

### ข้อเสนอแนะและแนวทางแก้ไขเบื้องต้น
- ศึกษา Indicator ที่สามารถช่วย detect sideway ให้ดีขึ้น
"""