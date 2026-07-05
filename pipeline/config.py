"""
全球资产流向 Pipeline — 配置文件
"""

# 数据存储路径
DATA_RAW = "data/raw"
DATA_PROCESSED = "data/processed"
REPORTS_DIR = "reports"

# 目标城市配置
# base_currency: 计算汇率调整后收益时使用的基础货币
CITIES = [
    {"city": "Tokyo",       "country": "Japan",       "currency": "JPY", "fred_fx": "DEXJPUS"},
    {"city": "Singapore",   "country": "Singapore",   "currency": "SGD", "fred_fx": "DEXSIUS"},
    {"city": "Dubai",       "country": "UAE",          "currency": "AED", "fred_fx": None},          # AED 盯住美元，用固定汇率
    {"city": "Sydney",      "country": "Australia",   "currency": "AUD", "fred_fx": "DEXUSAL"},
    {"city": "London",      "country": "UK",           "currency": "GBP", "fred_fx": "DEXUSUK"},
    {"city": "New York",    "country": "USA",          "currency": "USD", "fred_fx": None},           # 基准货币
    {"city": "Shanghai",    "country": "China",        "currency": "CNY", "fred_fx": "DEXCHUS"},
    {"city": "Hong Kong",   "country": "HongKong",    "currency": "HKD", "fred_fx": "DEXHKUS"},
]

# FRED API
FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
FRED_API_KEY = "f601a37366c8923ba92f029eb29bb026"

# ExchangeRate-API（备用）
FX_BASE = "https://v6.exchangerate-api.com/v6"
FX_API_KEY = ""   # 免费版每月 1500 次

# BIS Property Prices CSV URL
BIS_PROPERTY_URL = "https://www.bis.org/statistics/pp/pp_detailed.xlsx"

# OECD Housing Prices API
OECD_HOUSE_URL = "https://sdmx.oecd.org/public/rest/data/OECD.ECO.MPD,DSD_AN_HOUSE_PRICES@DF_HOUSE_PRICES,1.1/all?format=csvfilewithlabels"

# 新加坡 URA API（私人住宅成交）
URA_TOKEN_URL = "https://www.ura.gov.sg/uraDataService/insertNewToken.action"
URA_TRANSACTIONS_URL = "https://www.ura.gov.sg/uraDataService/invokeUraDS?service=PMI_Resi_Transaction"
URA_ACCESS_KEY = ""  # 注册：https://www.ura.gov.sg/maps/api/

# 日本国土交通省不动产交易 API
JAPAN_TRADE_URL = "https://www.land.mlit.go.jp/webland/api/TradeListSearch"

# 迪拜 DLD 开放数据（CSV 下载）
DUBAI_DLD_URL = "https://dubailand.gov.ae/en/open-data/real-estate-data/#/"

# Zillow Research（CSV 文件直链）
ZILLOW_ZHVI_URL = "https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
ZILLOW_RENTAL_URL = "https://files.zillowstatic.com/research/public_csvs/zori/Metro_zori_uc_sfrcondomfr_sm_month.csv"

# 基础货币（用于计算跨国买家视角收益）
BASE_CURRENCY = "CNY"  # 中国买家视角
