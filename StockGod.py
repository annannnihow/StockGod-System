# -*- coding: utf-8 -*-
import sys, os, random, requests, urllib3
import numpy as np
import pandas as pd
from datetime import datetime
import yfinance as yf
import warnings

# 關閉不必要的警告提示
warnings.filterwarnings('ignore')
# 🛡️ 關閉 requests 使用 verify=False 時產生的安全警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 確保 Windows 終端機正常顯示中文，避免亂碼
if sys.platform.startswith('win'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

print("="*80)
print(" 🚀【少年股神飆股大師】全自動多市場巡航系統 (SSL突破版)")
print(" 🎯 核心目標：挖掘具備爆發動能、且流動性安全之超級強勢股")
print(" 📊 運算引擎：多因子 PR 位階大對比 + 殭屍股防護盾")
print("="*80)

# ==========================================
# 📋 [模組一] 自動化市場觀測池與參數設定
# ==========================================
def fetch_tickers(market_choice):
    watchlist = {}
    
    if market_choice == '1':
        print("📋 [1/3] 正在連線至 NASDAQ 官方伺服器，下載美股名單...")
        volume_threshold = 500000 
        try:
            url = "ftp://ftp.nasdaqtrader.com/symboldirectory/nasdaqtraded.txt"
            df = pd.read_csv(url, sep='|')
            df = df[(df['Test Issue'] == 'N') & (df['ETF'] == 'N')]
            tickers = [str(t) for t in df['Symbol'].dropna().tolist() if '$' not in str(t) and '.' not in str(t)]
            
            selected = random.sample(tickers, min(6000, len(tickers)))
            for s in selected: watchlist[s] = {"name": s}
            return watchlist, volume_threshold
        except Exception as e:
            print(f"❌ 美股名單下載失敗 ({e})，載入備用名單...")
            selected = ["AAPL", "TSLA", "NVDA", "AMD", "MSFT", "GOOGL", "META"]
            return {s: {"name": s} for s in selected}, volume_threshold
            
    else:
        print("📋 [1/3] 正在連線至【台灣證交所 Open API】，嘗試下載全市場名單...")
        volume_threshold = 1000000
        try:
            url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
            }
            
            # 🛡️ 關鍵修復：加入 verify=False 強行繞過 SSL 憑證驗證
            res = requests.get(url, headers=headers, timeout=15, verify=False)
            res.raise_for_status() 
            data = res.json()
            
            tw_tickers = []
            for item in data:
                code = item['Code']
                name = item['Name']
                if len(code) == 4 and code.isdigit():
                    symbol = f"{code}.TW"
                    watchlist[symbol] = {"name": name}
                    tw_tickers.append(symbol)
            
            print(f"✅ 成功突破防火牆！抓取 {len(tw_tickers)} 檔上市普通股。")
            selected = random.sample(tw_tickers, min(1000, len(tw_tickers)))
            return {s: watchlist[s] for s in selected}, volume_threshold
            
        except Exception as e:
            print(f"⚠️ 證交所 API 連線不穩 ({e})")
            print("🛡️ 啟動【台股 Top 50 核心備援庫】繼續執行任務...")
            
            # 🎯 關鍵修復：修正上櫃股後綴為 .TWO (如 3293 鈊象)
            tw_backup = {
                "2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科", "2308.TW": "台達電", "2382.TW": "廣達",
                "2881.TW": "富邦金", "2882.TW": "國泰金", "2603.TW": "長榮", "3231.TW": "緯創", "2891.TW": "中信金",
                "2412.TW": "中華電", "2886.TW": "兆豐金", "3711.TW": "日月光", "1216.TW": "統一", "2884.TW": "玉山金",
                "2002.TW": "中鋼", "2609.TW": "陽明", "2303.TW": "聯電", "2885.TW": "元大金", "5880.TW": "合庫金",
                "2892.TW": "第一金", "2357.TW": "華碩", "3045.TW": "台灣大", "2395.TW": "研華", "2880.TW": "華南金",
                "2379.TW": "瑞昱", "6669.TW": "緯穎", "2883.TW": "開發金", "4904.TW": "遠傳", "2912.TW": "統一超",
                "3008.TW": "大立光", "2345.TW": "智邦", "3034.TW": "聯詠", "2324.TW": "仁寶", "1101.TW": "台泥",
                "2356.TW": "英業達", "2615.TW": "萬海", "1519.TW": "華城", "2890.TW": "永豐金", "2887.TW": "台新金",
                "2301.TW": "光寶科", "1605.TW": "華新", "2408.TW": "南亞科", "1504.TW": "東元", "3293.TWO": "鈊象",
                "2376.TW": "技嘉", "3661.TW": "世芯-KY", "3443.TW": "創意", "2449.TW": "京元電", "3017.TW": "奇鋐"
            }
            return {k: {"name": v} for k, v in tw_backup.items()}, volume_threshold

# ==========================================
# 🚀 [主程序] 歷史數據解析與大師計分板
# ==========================================
def main():
    print("\n👉 請選擇要掃描的市場：")
    print("  [1] 美股 (US Market)")
    print("  [2] 台股 (Taiwan Market - 上市及權值股)")
    market = input("請輸入 1 或 2，然後按 Enter： ").strip()
    if market not in ['1', '2']: market = '1'

    watchlist, MIN_VOLUME = fetch_tickers(market)
    target_symbols = list(watchlist.keys())
    
    print(f"✅ 成功鎖定 {len(target_symbols)} 檔監控目標。流動性門檻設定：{MIN_VOLUME:,} 股")
    print("⛏️ [2/3] 展開歷史數據海量下載與特徵運算...")
    
    chunk_size = 50 
    analyzed_data = []
    period_days = "100d" if market == '1' else "150d"
    
    for i in range(0, len(target_symbols), chunk_size):
        current_chunk = target_symbols[i:i+chunk_size]
        print(f"   當前進度: {min(i+chunk_size, len(target_symbols))}/{len(target_symbols)}...", end='\r')
        
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

                    # 🎯 濾除 .TW 或是 .TWO 後綴，讓報表顯示乾淨代碼
                    clean_ticker = symbol.replace('.TW', '').replace('.TWO', '')
                    
                    analyzed_data.append({
                        'Ticker': clean_ticker, 
                        'Company': watchlist[symbol]['name'], 
                        'Price': current_price,
                        'Vol_5D': avg_vol_5,
                        'MA5': avg_5,
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

    print("\n✅ 數據運算完畢！準備執行多因子 PR 位階大排行... [3/3]")
    
    df_results = pd.DataFrame(analyzed_data)
    if df_results.empty:
        print("❌ 缺乏有效運算數據 (可能全數跌破均線或未達流動性門檻)。")
        return

    factor_columns = ['Score_Vol', 'Score_Band', 'Score_Quarter', 'Score_Trend', 'Score_Month', 'Score_BandTop', 'Score_10D']
    factor_weights = [15.0, 20.0, 15.0, 15.0, 15.0, 10.0, 10.0] if market == '2' else [29.08, 19.33, 10.39, 7.67, 7.26, 5.09, 4.25]

    for col in factor_columns:
        df_results[col + '_Rank'] = df_results[col].rank(pct=True)

    df_results['Master_Score'] = 0.0
    for col, w in zip(factor_columns, factor_weights):
        df_results['Master_Score'] += df_results[col + '_Rank'] * w

    df_results['Master_Score'] = (df_results['Master_Score'] / sum(factor_weights)) * 100

    df_survivors = df_results[df_results['Price'] >= df_results['MA5']].copy()
    top_20_stocks = df_survivors.sort_values(by='Master_Score', ascending=False).head(20)

    market_name = "美股" if market == '1' else "台股"
    print("\n" + "="*80)
    print(f" 👑 本日【{market_name}】最強潛力名單 (產出時間: {datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print("="*80)
    print(f"{'排名':<4} | {'代碼':<6} | {'企業名稱':<10} | {'最新報價':<8} | {'5日均量(股)':<12} | {'綜合評分':<6}")
    print("-" * 80)

    for idx, (_, row) in enumerate(top_20_stocks.iterrows(), 1):
        comp_name = str(row['Company'])[:8]
        print(f"{idx:<4} | {row['Ticker']:<6} | {comp_name:　<5} | {row['Price']:<8.2f} | {int(row['Vol_5D']):<12,} | {row['Master_Score']:>6.2f}")
        
    print("="*80)

    try:
        current_dir = os.getcwd() 
        file_name = f"StockGod_Top20_{market_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        file_path = os.path.join(current_dir, file_name)
        top_20_stocks.to_csv(file_path, index=False, encoding='utf-8-sig')
        print(f"\n📁 實戰清單已成功匯出！\n📍 檔案位置 👉 {file_path}")
    except Exception as e: 
        print(f"\n❌ 存檔失敗: {e}")

if __name__ == "__main__":
    main()