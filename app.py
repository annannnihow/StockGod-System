# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import random
import urllib3
from datetime import datetime

# 關閉不必要的警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 🎨 網頁基礎設定 (這段會讓網頁看起來更專業)
# ==========================================
st.set_page_config(page_title="少年股神飆股大師", page_icon="🚀", layout="wide")
st.title("🚀【少年股神飆股大師】全自動巡航系統")
st.markdown("🎯 **核心目標：** 挖掘具備爆發動能、且流動性安全之超級強勢股")
st.markdown("---")

# ==========================================
# 📋 [模組一] 抓取觀測池 (加入快取機制，避免每次按按鈕都要重新抓清單)
# ==========================================
@st.cache_data(ttl=3600) # 快取 1 小時，加速網頁載入
def fetch_tickers(market_choice):
    watchlist = {}
    if market_choice == '美股':
        volume_threshold = 500000 
        try:
            url = "ftp://ftp.nasdaqtrader.com/symboldirectory/nasdaqtraded.txt"
            df = pd.read_csv(url, sep='|')
            df = df[(df['Test Issue'] == 'N') & (df['ETF'] == 'N')]
            tickers = [str(t) for t in df['Symbol'].dropna().tolist() if '$' not in str(t) and '.' not in str(t)]
            selected = random.sample(tickers, min(6000, len(tickers)))
            for s in selected: watchlist[s] = {"name": s}
            return watchlist, volume_threshold
        except:
            return {s: {"name": s} for s in ["AAPL", "TSLA", "NVDA", "AMD", "MSFT"]}, volume_threshold
    else:
        volume_threshold = 1000000
        try:
            url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(url, headers=headers, timeout=15, verify=False)
            data = res.json()
            tw_tickers = []
            for item in data:
                code = item['Code']
                if len(code) == 4 and code.isdigit():
                    symbol = f"{code}.TW"
                    watchlist[symbol] = {"name": item['Name']}
                    tw_tickers.append(symbol)
            selected = random.sample(tw_tickers, min(1086, len(tw_tickers)))
            return {s: watchlist[s] for s in selected}, volume_threshold
        except:
            tw_backup = {"2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科", "2308.TW": "台達電"}
            return {k: {"name": v} for k, v in tw_backup.items()}, volume_threshold

# ==========================================
# 🎛️ 網頁側邊欄設定 (控制面板)
# ==========================================
st.sidebar.header("⚙️ 巡航參數設定")
market = st.sidebar.selectbox("👉 選擇要掃描的市場：", ["美股", "台股"])
start_scan = st.sidebar.button("🔥 啟動全自動掃描", use_container_width=True)

# ==========================================
# 🚀 主程序：當按下按鈕時才執行
# ==========================================
if start_scan:
    watchlist, MIN_VOLUME = fetch_tickers(market)
    target_symbols = list(watchlist.keys())
    
    # 在網頁上顯示進度狀態
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    status_text.info(f"✅ 成功鎖定 {len(target_symbols)} 檔監控目標。流動性門檻：{MIN_VOLUME:,} 股")
    
    chunk_size = 50 
    analyzed_data = []
    period_days = "100d" if market == '美股' else "150d"
    
    # 模擬進度條運作
    for i in range(0, len(target_symbols), chunk_size):
        current_chunk = target_symbols[i:i+chunk_size]
        
        # 更新進度條
        progress = min((i + chunk_size) / len(target_symbols), 1.0)
        progress_bar.progress(progress)
        status_text.text(f"⛏️ 正在下載歷史數據與特徵運算... (進度: {int(progress*100)}%)")
        
        try:
            market_data = yf.download(current_chunk, period=period_days, interval="1d", progress=False)
            for symbol in current_chunk:
                try:
                    if len(current_chunk) == 1:
                        price_close = market_data['Close']
                        volume_data = market_data['Volume']
                    else:
                        price_close = market_data['Close'][symbol]
                        volume_data = market_data['Volume'][symbol]
                        
                    price_close = price_close.dropna()
                    volume_data = volume_data.dropna()
                    
                    if price_close.empty or len(price_close) < 60 or volume_data.empty: continue
                    
                    avg_vol_5 = volume_data.rolling(5).mean().iloc[-1]
                    if avg_vol_5 < MIN_VOLUME: continue  
                    
                    avg_5 = price_close.rolling(5).mean().iloc[-1]
                    avg_20 = price_close.rolling(20).mean().iloc[-1]
                    avg_60 = price_close.rolling(60).mean().iloc[-1]
                    daily_change = price_close.pct_change()
                    volatility = daily_change.rolling(20).std().iloc[-1] * np.sqrt(252) * 100
                    std_20 = price_close.rolling(20).std().iloc[-1]
                    band_top = avg_20 + 2 * std_20
                    band_bottom = avg_20 - 2 * std_20
                    band_expansion = (band_top - band_bottom) / avg_20 * 100 if avg_20 != 0 else 0
                    
                    current_price = price_close.iloc[-1]
                    gap_to_quarter = (current_price / avg_60 - 1) * 100 if avg_60 != 0 else 0
                    trend_momentum = (avg_5 / avg_60 - 1) * 100 if avg_60 != 0 else 0
                    gap_to_month = (current_price / avg_20 - 1) * 100 if avg_20 != 0 else 0
                    gap_to_band_top = (current_price / band_top - 1) * 100 if band_top != 0 else 0
                    past_price = price_close.iloc[-11]
                    jump_10_days = (current_price - past_price) / past_price * 100 if past_price != 0 else 0
                    
                    if np.isnan(volatility): continue
                    
                    clean_ticker = symbol.replace('.TW', '').replace('.TWO', '')
                    analyzed_data.append({
                        '代碼': clean_ticker, 
                        '企業名稱': watchlist[symbol]['name'], 
                        '最新報價': round(current_price, 2),
                        '5日均量(股)': int(avg_vol_5),
                        'Score_Vol': volatility,
                        'Score_Band': band_expansion,
                        'Score_Quarter': gap_to_quarter,
                        'Score_Trend': trend_momentum,
                        'Score_Month': gap_to_month,
                        'Score_BandTop': gap_to_band_top,
                        'Score_10D': jump_10_days
                    })
                except: continue
        except: continue

    # 完成運算後清除狀態列
    status_text.empty()
    progress_bar.empty()
    
    df_results = pd.DataFrame(analyzed_data)
    
    if df_results.empty:
        st.error("❌ 缺乏有效運算數據 (可能全數跌破均線或未達流動性門檻)。")
    else:
        # --- 核心演算法 ---
        factor_columns = ['Score_Vol', 'Score_Band', 'Score_Quarter', 'Score_Trend', 'Score_Month', 'Score_BandTop', 'Score_10D']
        factor_weights = [15.0, 20.0, 15.0, 15.0, 15.0, 10.0, 10.0] if market == '台股' else [29.08, 19.33, 10.39, 7.67, 7.26, 5.09, 4.25]

        for col in factor_columns:
            df_results[col + '_Rank'] = df_results[col].rank(pct=True)

        df_results['綜合評分'] = 0.0
        for col, w in zip(factor_columns, factor_weights):
            df_results['綜合評分'] += df_results[col + '_Rank'] * w
        df_results['綜合評分'] = round((df_results['綜合評分'] / sum(factor_weights)) * 100, 2)

        # 整理最後顯示的表格
        display_cols = ['代碼', '企業名稱', '最新報價', '5日均量(股)', '綜合評分']
        final_df = df_results[display_cols].sort_values(by='綜合評分', ascending=False).head(20)
        
        # 加上名次當作 Index
        final_df.index = np.arange(1, len(final_df) + 1)
        final_df.index.name = '排名'

        # ==========================================
        # 📊 輸出超炫網頁表格
        # ==========================================
        st.success(f"🎉 運算完畢！產出時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        st.subheader(f"👑 本日【{market}】最強 20 大潛力名單")
        
        # 使用 st.dataframe 讓網頁畫出互動式表格 (可以點擊欄位排序)
        st.dataframe(final_df, use_container_width=True)
        
        # 提供 CSV 下載按鈕
        csv = final_df.to_csv(encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="📥 下載實戰清單 (CSV)",
            data=csv,
            file_name=f"StockGod_Top20_{market}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv',
        )
else:
    # 還沒按下按鈕時顯示的預設畫面
    st.info("👈 請在左側選單選擇市場，並點擊「啟動全自動掃描」。")