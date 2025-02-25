"""A module to contain all project-wide constants."""

from curses.ascii import VT
from ctypes.wintypes import HDC
from typi

from holidays import MARng import Literal
import re

OBB_EQUITY_PRICE_QUOTE_PROVIDERS = Literal[
    "cboe", "fmp", "intrinio", "tmx", "tradier", "yfinance"
]

OBB_EQUITY_PROFILE_PROVIDERS = Literal[
    "finviz", "fmp", "intrinio", "tmx", "yfinance"
]

OBB_ETF_INFO_PROVIDERS = Literal["fmp", "intrinio", "tmx", "yfinance"]

OBB_EQUITY_PRICE_HISTORICAL_PROVIDERS = Literal[
    "alpha_vantage",
    "cboe",
    "fmp",
    "intrinio",
    "polygon",
    "tiingo",
    "tmx",
    "tradier",
    "yfinance",
]

ASSET_CLASSES = Literal[
    "Fixed Income",
    "Foreign Exchange",
    "Equity",
    "Commodity",
    "Cash",
    "Crypto",
    "Gold",
    "Credit",
]
ASSET_CLASS_MAPPING: dict[str, ASSET_CLASSES] = {
    "Fixed Income": "Fixed Income",
    "Ultrashort Bond": "Fixed Income",
    "Bond": "Fixed Income",
    r".*\s?Bond.*": "Fixed Income",
    "Foreign Exchange": "Foreign Exchange",
    "Single Currency": "Foreign Exchange",
    "Forex": "Foreign Exchange",
    "FX": "Foreign Exchange",
    "Equity": "Equity",
    "Stocks": "Equity",
    "Commodity": "Commodity",
    "Commodities": "Commodity",
    r".*Commodities.*": "Commodity",
    "Cash": "Cash",
    "Money Market": "Cash",
    "Crypto": "Crypto",
    "Digital Assets": "Crypto",
    "Cryptocurrency": "Crypto",
    "Gold": "Gold",
    "Precious Metals": "Gold",
    "Credit": "Credit",
    "Debt": "Credit",
}

GICS_SECTORS = Literal[
    "Communication Services",
    "Consumer Cyclical",
    "Consumer Defensive",
    "Energy",
    "Financials",
    "Health Care",
    "Industrials",
    "Technology",
    "Materials",
    "Real Estate",
    "Utilities",
]
GICS_SECTOR_MAPPING: dict[str, GICS_SECTORS] = {
    "Communication Services": "Communication Services",
    "Communications": "Communication Services",
    "Communication": "Communication Services",
    "Consumer Cyclical": "Consumer Cyclical",
    "Consumer Discretionary": "Consumer Cyclical",
    "Consumer Defensive": "Consumer Defensive",
    "Consumer Staples": "Consumer Defensive",
    "Energy": "Energy",
    "Equity Energy": "Energy",
    "Financials": "Financials",
    "Financial Service": "Financials",
    "Financial": "Financials",
    "Health Care": "Health Care",
    "Healthcare": "Health Care",
    "Industrials": "Industrials",
    "Technology": "Technology",
    "Materials": "Materials",
    "Basic Materials": "Materials",
    "Real Estate": "Real Estate",
    "Utilities": "Utilities",
}

# Common US ETFs by category
# This is not an exhaustive list of all ETFs in the US market
# but rather a collection of popular and widely traded ETFs

# Broad Market ETFs
BROAD_MARKET_ETFS: list[str] = [
    "SPY",  # SPDR S&P 500 ETF Trust
    "IVV",  # iShares Core S&P 500 ETF
    "VOO",  # Vanguard S&P 500 ETF
    "QQQ",  # Invesco QQQ Trust (Nasdaq-100)
    "DIA",  # SPDR Dow Jones Industrial Average ETF
    "IWM",  # iShares Russell 2000 ETF
    "VTI",  # Vanguard Total Stock Market ETF
    "ITOT",  # iShares Core S&P Total U.S. Stock Market ETF
    "RSP",  # Invesco S&P 500 Equal Weight ETF
    "SPLG",  # SPDR Portfolio S&P 500 ETF
]

# Sector ETFs
SECTOR_ETFS: list[str] = [
    # Technology
    "XLK",  # Technology Select Sector SPDR Fund
    "VGT",  # Vanguard Information Technology ETF
    "SMH",  # VanEck Semiconductor ETF
    "SOXX",  # iShares Semiconductor ETF
    # Healthcare
    "XLV",  # Health Care Select Sector SPDR Fund
    "VHT",  # Vanguard Health Care ETF
    "IBB",  # iShares Biotechnology ETF
    # Financials
    "XLF",  # Financial Select Sector SPDR Fund
    "VFH",  # Vanguard Financials ETF
    "KRE",  # SPDR S&P Regional Banking ETF
    # Energy
    "XLE",  # Energy Select Sector SPDR Fund
    "VDE",  # Vanguard Energy ETF
    # Consumer
    "XLY",  # Consumer Discretionary Select Sector SPDR Fund
    "XLP",  # Consumer Staples Select Sector SPDR Fund
    "VDC",  # Vanguard Consumer Staples ETF
    # Utilities
    "XLU",  # Utilities Select Sector SPDR Fund
    "VPU",  # Vanguard Utilities ETF
    # Real Estate
    "XLRE",  # Real Estate Select Sector SPDR Fund
    "VNQ",  # Vanguard Real Estate ETF
    # Communication Services
    "XLC",  # Communication Services Select Sector SPDR Fund
    # Materials
    "XLB",  # Materials Select Sector SPDR Fund
    "VAW",  # Vanguard Materials ETF
    # Industrials
    "XLI",  # Industrial Select Sector SPDR Fund
    "VIS",  # Vanguard Industrials ETF
]

# Bond/Fixed Income ETFs
BOND_ETFS: list[str] = [
    "AGG",  # iShares Core U.S. Aggregate Bond ETF
    "BND",  # Vanguard Total Bond Market ETF
    "LQD",  # iShares iBoxx $ Investment Grade Corporate Bond ETF
    "HYG",  # iShares iBoxx $ High Yield Corporate Bond ETF
    "JNK",  # SPDR Bloomberg High Yield Bond ETF
    "TLT",  # iShares 20+ Year Treasury Bond ETF
    "IEF",  # iShares 7-10 Year Treasury Bond ETF
    "SHY",  # iShares 1-3 Year Treasury Bond ETF
    "GOVT",  # iShares U.S. Treasury Bond ETF
    "MUB",  # iShares National Muni Bond ETF
    "VTEB",  # Vanguard Tax-Exempt Bond ETF
    "BNDX",  # Vanguard Total International Bond ETF
    "EMB",  # iShares J.P. Morgan USD Emerging Markets Bond ETF
    "TIPS",  # iShares TIPS Bond ETF
]

# International ETFs
INTERNATIONAL_ETFS: list[str] = [
    "VXUS",  # Vanguard Total International Stock ETF
    "EFA",  # iShares MSCI EAFE ETF
    "VEA",  # Vanguard FTSE Developed Markets ETF
    "EEM",  # iShares MSCI Emerging Markets ETF
    "VWO",  # Vanguard FTSE Emerging Markets ETF
    "IEMG",  # iShares Core MSCI Emerging Markets ETF
    "FXI",  # iShares China Large-Cap ETF
    "EWJ",  # iShares MSCI Japan ETF
    "EWG",  # iShares MSCI Germany ETF
    "EWU",  # iShares MSCI United Kingdom ETF
    "EWC",  # iShares MSCI Canada ETF
    "EWZ",  # iShares MSCI Brazil ETF
    "EWY",  # iShares MSCI South Korea ETF
    "EWA",  # iShares MSCI Australia ETF
]

# Commodity ETFs
COMMODITY_ETFS: list[str] = [
    "GLD",  # SPDR Gold Shares
    "IAU",  # iShares Gold Trust
    "SLV",  # iShares Silver Trust
    "USO",  # United States Oil Fund
    "UNG",  # United States Natural Gas Fund
    "DBC",  # Invesco DB Commodity Index Tracking Fund
    "PDBC",  # Invesco Optimum Yield Diversified Commodity Strategy
    "COMT",  # iShares GSCI Commodity Dynamic Roll Strategy ETF
    "CPER",  # United States Copper Index Fund
    "WEAT",  # Teucrium Wheat Fund
    "CORN",  # Teucrium Corn Fund
]

# Volatility ETFs
VOLATILITY_ETFS: list[str] = [
    "UVXY",  # ProShares Ultra VIX Short-Term Futures ETF
    "SVXY",  # ProShares Short VIX Short-Term Futures ETF
    "VXX",  # iPath Series B S&P 500 VIX Short-Term Futures ETN
]

# Leveraged ETFs
LEVERAGED_ETFS: list[str] = [
    "TQQQ",  # ProShares UltraPro QQQ (3x Nasdaq-100)
    "SQQQ",  # ProShares UltraPro Short QQQ (3x Inverse Nasdaq-100)
    "UPRO",  # ProShares UltraPro S&P 500 (3x S&P 500)
    "SPXU",  # ProShares UltraPro Short S&P 500 (3x Inverse S&P 500)
    "SSO",  # ProShares Ultra S&P 500 (2x S&P 500)
    "SDS",  # ProShares UltraShort S&P 500 (2x Inverse S&P 500)
    "TNA",  # Direxion Daily Small Cap Bull 3X Shares
    "TZA",  # Direxion Daily Small Cap Bear 3X Shares
    "SPXL",  # Direxion Daily S&P 500 Bull 3X Shares
    "SPXS",  # Direxion Daily S&P 500 Bear 3X Shares
]

# Thematic ETFs
THEMATIC_ETFS: list[str] = [
    # Technology Themes
    "ARKK",  # ARK Innovation ETF
    "ARKW",  # ARK Next Generation Internet ETF
    "ARKG",  # ARK Genomic Revolution ETF
    "ARKF",  # ARK Fintech Innovation ETF
    "ARKX",  # ARK Space Exploration & Innovation ETF
    "BOTZ",  # Global X Robotics & Artificial Intelligence ETF
    "ROBO",  # ROBO Global Robotics and Automation Index ETF
    "FINX",  # Global X FinTech ETF
    "HACK",  # ETFMG Prime Cyber Security ETF
    "CIBR",  # First Trust NASDAQ Cybersecurity ETF
    "SKYY",  # First Trust Cloud Computing ETF
    "WCLD",  # WisdomTree Cloud Computing Fund
    "ESPO",  # VanEck Video Gaming and eSports ETF
    "HERO",  # Global X Video Games & Esports ETF
    "SOCL",  # Global X Social Media ETF
    "IBUY",  # Amplify Online Retail ETF
    "ONLN",  # ProShares Online Retail ETF
    # Clean Energy/ESG
    "ICLN",  # iShares Global Clean Energy ETF
    "TAN",  # Invesco Solar ETF
    "FAN",  # First Trust Global Wind Energy ETF
    "PBW",  # Invesco WilderHill Clean Energy ETF
    "QCLN",  # First Trust NASDAQ Clean Edge Green Energy Index Fund
    "ESGU",  # iShares ESG Aware MSCI USA ETF
    "ESGV",  # Vanguard ESG U.S. Stock ETF
    # Cannabis
    "MSOS",  # AdvisorShares Pure US Cannabis ETF
    "MJ",  # ETFMG Alternative Harvest ETF
    # Other Themes
    "JETS",  # U.S. Global Jets ETF
    "AWAY",  # ETFMG Travel Tech ETF
    "BETZ",  # Roundhill Sports Betting & iGaming ETF
    "NERD",  # Roundhill BITKRAFT Esports & Digital Entertainment ETF
    "MOON",  # Direxion Moonshot Innovators ETF
    "GNOM",  # Global X Genomics & Biotechnology ETF
]

# Dividend ETFs
DIVIDEND_ETFS: list[str] = [
    "VYM",  # Vanguard High Dividend Yield ETF
    "SCHD",  # Schwab U.S. Dividend Equity ETF
    "HDV",  # iShares Core High Dividend ETF
    "DVY",  # iShares Select Dividend ETF
    "SDY",  # SPDR S&P Dividend ETF
    "SPYD",  # SPDR Portfolio S&P 500 High Dividend ETF
    "SPHD",  # Invesco S&P 500 High Dividend Low Volatility ETF
    "DGRO",  # iShares Core Dividend Growth ETF
    "VIG",  # Vanguard Dividend Appreciation ETF
    "NOBL",  # ProShares S&P 500 Dividend Aristocrats ETF
]

# Cryptocurrency ETFs/ETPs
CRYPTO_ETFS: list[str] = [
    "BITO",  # ProShares Bitcoin Strategy ETF
    "GBTC",  # Grayscale Bitcoin Trust
    "ETHE",  # Grayscale Ethereum Trust
    "BITQ",  # Bitwise Crypto Industry Innovators ETF
    "BLOK",  # Amplify Transformational Data Sharing ETF
    "BLCN",  # Siren Nasdaq NexGen Economy ETF
    "DAPP",  # VanEck Digital Transformation ETF
]

# Combine all ETF categories into one comprehensive list
US_ETF_SYMBOLS: list[str] = (
    BROAD_MARKET_ETFS
    + SECTOR_ETFS
    + BOND_ETFS
    + INTERNATIONAL_ETFS
    + COMMODITY_ETFS
    + VOLATILITY_ETFS
    + LEVERAGED_ETFS
    + THEMATIC_ETFS
    + DIVIDEND_ETFS
    + CRYPTO_ETFS
)

# Remove any duplicates while preserving order
US_ETF_SYMBOLS = list(dict.fromkeys(US_ETF_SYMBOLS))


US_TOTAL_MARKET_ETF_SYMBOLS: list[str] = [
    "ABLG", "ACLC", "ACLO", "ACVF", "ADME", "ADPV", "AESR", "AFIF", "AFIX", "AFLG", "AGGH", "AGOX", "AGZD", "AIEQ", "AINP", "AIPI", "AIVL", "ALTL", "AMDL", "AMDY", "AMZA", "AMZU", "AMZY", "AOHY", "AOK", "APLU", "APLY", "APMU", "APRW", "AQLT", "ARKX", "ATMP", "AUGW", "AUSF", "AVES", "AVGE", "AVGV", "AVIV", "AVLC", "AVMC", "AVMU", "AVMV", "AVRE", "AVSD", "AVSF", "AVSU", "BABX", "BALI", "BAPR", "BAUG", "BBH", "BBLU", "BBSC", "BCD", "BCHP", "BDEC", "BEEX", "BFEB", "BFOR", "BGIG", "BGRN", "BIBL", "BINV", "BITQ", "BJAN", "BJUL", "BJUN", "BKCH", "BKCI", "BKEM", "BKHY", "BKMC", "BKSE", "BKUI", "BLES", "BMAR", "BMAY", "BNDC", "BNKU", "BNOV", "BOCT", "BOIL", "BRNY", "BRTR", "BRZU", "BSCX", "BSCY", "BSEP", "BSJO", "BSJR", "BSJS", "BSJT", "BSMO", "BSMP", "BSMQ", "BSMR", "BSMS", "BSMT", "BSMU", "BTAL", "BTCW", "BUCK", "BUFB", "BUFF", "BUFG", "BUFT", "BUFZ", "BUSA", "BUXX", "BWZ", "BYLD", "CAFX", "CAML", "CAOS", "CAPE", "CARK", "CARY", "CCNR", "CDL", "CDX", "CEFS", "CEMB", "CERY", "CFA", "CFO", "CGCV", "CGGE", "CGHM", "CGIE", "CGNG", "CGSM", "CHAT", "CHAU", "CHGX", "CHIQ", "CLIP", "CLOU", "CLSE", "CLSM", "CMBS", "CMDT", "CMDY", "CNRG", "CNYA", "COM", "CPER", "CPLB", "CPLS", "CSB", "CSHI", "CSM", "CSMD", "CURE", "CVLC", "CVSB", "CVY", "CWEB", "CWS", "CXSE", "CZA", "DAPP", "DAPR", "DAUG", "DBAW", "DBB", "DBJP", "DBND", "DBO", "DBP", "DCRE", "DDEC", "DDLS", "DDM", "DDWM", "DECW", "DEHP", "DEUS", "DEW", "DEXC", "DFCA", "DFE", "DFEB", "DFEN", "DFJ", "DFNL", "DFSB", "DFSE", "DFVX", "DGCB", "DGP", "DGRE", "DGRS", "DGT", "DIAL", "DIM", "DINT", "DIVZ", "DJAN", "DJD", "DJIA", "DJP", "DJUL", "DJUN", "DMAR", "DMAY", "DMBS", "DNL", "DNOV", "DOCT", "DOG", "DOL", "DRIV", "DRLL", "DSEP", "DTCR", "DTH", "DUBS", "DWLD", "DWM", "DWUS", "DWX", "DXUV", "EALT", "ECH", "ECML", "EDEN", "EDGF", "EDIV", "EDOW", "EELV", "EEMA", "EEMS", "EFAX", "EIDO", "EIPX", "EIS", "EJAN", "ELM", "EMBD", "EMCS", "EMHC", "EMHY", "EMNT", "EMQQ", "ENFR", "EPOL", "EQIN", "EQL", "ERNZ", "ERTH", "ERX", "ESG", "ESPO", "ETHO", "ETHT", "ETHV", "ETHW", "EVSB", "EVSD", "EVSM", "EWD", "EWI", "EWJV", "EWM", "EWN", "EWQ", "EWZS", "EYLD", "EZA", "FAB", "FAD", "FAN", "FAZ", "FBCV", "FBL", "FBY", "FCAL", "FCG", "FCOR", "FCPI", "FCTE", "FDD", "FDEM", "FDEV", "FDG", "FDHY", "FDIG", "FDM", "FDMO", "FDT", "FDTX", "FDV", "FEM", "FEMB", "FEMS", "FEP", "FEPI", "FFLG", "FFOG", "FGD", "FGDL", "FHEQ", "FIAX", "FICS", "FIGB", "FIIG", "FINX", "FISR", "FIVA", "FJP", "FLBR", "FLCA", "FLCH", "FLCO", "FLDB", "FLKR", "FLMI", "FLRG", "FLRT", "FLSP", "FLTB", "FLTW", "FLV", "FM", "FMAG", "FMAT", "FMF", "FNGD", "FNGO", "FNGS", "FNK", "FNY", "FPXI", "FRI", "FSMB", "FTCB", "FTQI", "FTRB", "FTSD", "FTXL", "FTXN", "FTXO", "FUMB", "FUNL", "FVC", "FWD", "FXE", "FXF", "FXG", "FXN", "FXU", "FXY", "FXZ", "FYC", "FYLD", "FYT", "GAL", "GAPR", "GARP", "GAUG", "GBF", "GCC", "GCOR", "GDEC", "GDIV", "GDMA", "GDXU", "GFEB", "GFLW", "GGLL", "GGME", "GGUS", "GHYB", "GHYG", "GII", "GINN", "GJAN", "GJUL", "GJUN", "GLIN", "GLOF", "GMAR", "GMAY", "GMF", "GNMA", "GNOV", "GOCT", "GOOY", "GOVZ", "GPIQ", "GPIX", "GQI", "GQRE", "GREK", "GRNB", "GRPM", "GRW", "GSC", "GSEP", "GSPY", "GSSC", "GTEK", "GTIP", "GUSH", "GVIP", "GVLU", "GVUS", "GXC", "GXUS", "HAP", "HAPI", "HAPS", "HAWX", "HCMT", "HCRB", "HDRO", "HDUS", "HECO", "HEEM", "HEGD", "HEQT", "HEWJ", "HEZU", "HFGO", "HGER", "HIGH", "HKND", "HLAL", "HMOP", "HSCZ", "HTAB", "HYBB", "HYBI", "HYBL", "HYDW", "HYEM", "HYFI", "HYGH", "HYGW", "HYHG", "HYXF", "HYZD", "IAPR", "IBD", "IBDZ", "IBHD", "IBHE", "IBHG", "IBHH", "IBHI", "IBMM", "IBMN", "IBMO", "IBMP", "IBMQ", "IBMR", "IBND", "IBTJ", "IBTK", "IBTL", "IBTM", "IBTO", "IBUY", "ICLO", "IDGT", "IDHQ", "IDLV", "IDMO", "IDNA", "IDOG", "IDRV", "IDUB", "IDVO", "IEO", "IETC", "IEZ", "IFV", "IGBH", "IGHG", "IGLD", "IGOV", "IGPT", "IJAN", "IJUL", "ILTB", "IMFL", "IMTB", "INCM", "INCO", "INDS", "INTL", "IPAY", "IPKW", "IPO", "IQDF", "IQSI", "IQSM", "IQSU", "ISCB", "ISCF", "ISCV", "ISMD", "IVAL", "IVOL", "IWMI", "IWMY", "IXG", "IXP", "IYM", "IYZ", "JAJL", "JANT", "JANW", "JEMB", "JHEM", "JHSC", "JIG", "JIVE", "JMHI", "JMSI", "JNUG", "JOET", "JPEM", "JPIB", "JPIN", "JPMB", "JPME", "JPRE", "JPSE", "JPUS", "JPXN", "JSCP", "JSMD", "JSML", "JSTC", "JUCY", "JULW", "JUST", "JXI", "KAPR", "KBA", "KBWD", "KBWP", "KBWY", "KCE", "KCSH", "KJAN", "KJUL", "KLIP", "KMLM", "KOCT", "KORP", "KRBN", "LCTD", "LDDR", "LDSF", "LEMB", "LGH", "LQDH", "LQDW", "LRGC", "LRGE", "LSAF", "LSAT", "LSGR", "LVHD", "MAMB", "MARM", "MAXJ", "MBCC", "MBOX", "MBS", "MBSF", "MDIV", "METV", "MFDX", "MFSI", "MFUS", "MGMT", "MGNR", "MILN", "MINO", "MISL", "MJ", "MLN", "MLPB", "MMIN", "MMTM", "MNA", "MODL", "MOO", "MORT", "MOTI", "MPRO", "MRSK", "MSFO", "MSFU", "MSOS", "MSSM", "MSTB", "MSTZ", "MUSI", "MUST", "MVV", "MXI", "NAIL", "NANC", "NAPR", "NBCM", "NBCR", "NBOS", "NBSD", "NBSM", "NFLT", "NFLY", "NFTY", "NJAN", "NJUL", "NOCT", "NTSI", "NUBD", "NUDM", "NUEM", "NUGT", "NUKZ", "NUMG", "NUMV", "NUSB", "NVDX", "NXTG", "NZAC", "OACP", "OAIM", "OAKM", "OALC", "OBIL", "OCIO", "OCTT", "OCTW", "OGIG", "OMFS", "ONEV", "ONOF", "OPER", "OPTZ", "OSCV", "OSEA", "OVL", "OWNS", "PALC", "PALL", "PAPI", "PBDC", "PBE", "PBP", "PBW", "PCGG", "PDN", "PEJ", "PFFV", "PFIX", "PFLD", "PFUT", "PGHY", "PGJ", "PHB", "PHDG", "PHYD", "PHYL", "PICB", "PIN", "PINK", "PIO", "PIZ", "PJFG", "PJP", "PJUN", "PKB", "PLTU", "PLTY", "PMAR", "PMAY", "PMBS", "POWA", "PPIE", "PRAE", "PRFD", "PRN", "PSCH", "PSCI", "PSCT", "PSFF", "PSP", "PSQ", "PTBD", "PTF", "PTH", "PTIN", "PTIR", "PTL", "PTMC", "PTRB", "PULT", "PUTW", "PWRD", "PY", "PZT", "QABA", "QBER", "QBUF", "QCLN", "QDEC", "QDEF", "QFLR", "QHY", "QID", "QINT", "QIS", "QJUN", "QLC", "QLV", "QMAR", "QMOM", "QQA", "QQH", "QQQY", "QSPT", "QUVU", "QVAL", "QVMM", "QVMS", "QWLD", "RDTE", "REMX", "RFDI", "RFG", "RFV", "RISR", "RLY", "RMOP", "ROBT", "ROE", "ROUS", "RPAR", "RSHO", "RSPA", "RSPD", "RSPF", "RSPG", "RSPM", "RSPR", "RSPS", "RSPU", "RSSB", "RSST", "RSSY", "RTH", "RUNN", "RVNU", "RWM", "RWX", "RXI", "RZV", "SAMT", "SCHJ", "SCJ", "SCMB", "SCO", "SDCI", "SDG", "SDOW", "SDS", "SDVD", "SECR", "SEEM", "SEIE", "SEIM", "SEIQ", "SEIS", "SEIV", "SEIX", "SELV", "SFLO", "SGDJ", "SGDM", "SHDG", "SHE", "SHYD", "SHYL", "SHYM", "SIHY", "SIO", "SIXA", "SIXD", "SIXG", "SIXH", "SIXJ", "SIXL", "SIXO", "SIZE", "SKOR", "SLNZ", "SLVO", "SLVP", "SMAX", "SMB", "SMCY", "SMIZ", "SMLV", "SMMV", "SMOG", "SMOT", "SMRI", "SNSR", "SOCL", "SOFR", "SOXQ", "SPD", "SPDN", "SPFF", "SPHB", "SPRE", "SPSK", "SPUC", "SPUU", "SPXS", "SPXT", "SPYU", "SRET", "SRHQ", "SRVR", "SSUS", "STCE", "STOT", "STPZ", "STXG", "STXT", "SVAL", "SVIX", "SVXY", "SWAN", "TACK", "TAFM", "TAGG", "TAXF", "TAXX", "TBFC", "TBFG", "TBG", "TBT", "TBUX", "TDSC", "TDV", "TECB", "TEQI", "TFLR", "TFPN", "TGRT", "TGRW", "THD", "THNQ", "THYF", "TJUL", "TLTD", "TLTE", "TMAT", "TMFG", "TMFM", "TMSL", "TMV", "TOGA", "TOK", "TOLZ", "TOPT", "TOTR", "TPHD", "TPIF", "TPLC", "TPSC", "TPZ", "TSLQ", "TSLR", "TSLT", "TSME", "TSMX", "TSPX", "TUA", "TUG", "TUR", "TVAL", "TZA", "UAPR", "UAUG", "UBND", "UCO", "UCRD", "UDEC", "UEVM", "UFEB", "UGL", "UIVM", "UJAN", "UJUL", "ULST", "ULTY", "ULVM", "UMI", "UMMA", "UNG", "UOCT", "URNJ", "URTY", "USCI", "USDU", "USDX", "USEP", "USMF", "USNZ", "USOI", "USSE", "USSG", "UTEN", "UTES", "UTWO", "UUP", "UVIX", "UVXY", "UWM", "VALQ", "VBIL", "VBND", "VEGN", "VFMF", "VFMV", "VFQY", "VGSR", "VIDI", "VIXY", "VLU", "VNM", "VPLS", "VSDA", "VSLU", "VSMV", "VTEC", "VTEI", "VUSE", "VXX", "WCBR", "WCLD", "WDIV", "WEAT", "WEBL", "WEBS", "WGMI", "WIP", "WOOD", "WTAI", "WTMF", "WWJD", "XBJL", "XCCC", "XCOR", "XDEC", "XDTE", "XEMD", "XES", "XHE", "XHYT", "XJH", "XJUN", "XMAR", "XMPT", "XMVM", "XONE", "XOVR", "XPH", "XRT", "XSEP", "XSHQ", "XSLV", "XSVN", "XSW", "XTEN", "XTL", "XTN", "XTRE", "XTWO", "XVV", "YBIT", "YBTC", "YJUN", "YLD", "YMAG", "YYY", "ZALT", "ZDEK", "ZECP", "ZTRE", "ZTWO"
]