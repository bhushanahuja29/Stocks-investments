# Indian Stocks Support - Requirements Specification

## Overview
Add support for Indian stock market (NSE/BSE) to the Crypto Levels Bhushan application, enabling users to find support/resistance zones for Indian stocks using the existing V3/V4 algorithms.

## User Stories

### US-1: Search Indian Stocks
**As a** trader  
**I want to** search for support zones in Indian stocks (NSE/BSE)  
**So that** I can identify key price levels for trading decisions

**Acceptance Criteria:**
- User can select "Indian Stocks (NSE/BSE)" from market type dropdown
- User can enter Indian stock symbols (e.g., RELIANCE, TCS, INFY)
- System automatically appends .NSE suffix for TwelveData API
- System fetches historical data using TwelveData API
- System computes zones using V3 or V4 algorithm based on user selection
- Results display zones with Indian Rupee (₹) currency symbol

### US-2: Monitor Indian Stock Levels
**As a** trader  
**I want to** monitor Indian stock price levels  
**So that** I get alerts when price reaches support/resistance zones

**Acceptance Criteria:**
- User can push Indian stock zones to monitoring dashboard
- System fetches current prices for Indian stocks using TwelveData API
- System displays prices in Indian Rupees (₹)
- System triggers alerts when price crosses monitored levels
- Market type is stored and preserved in MongoDB

### US-3: No API Quota Concerns
**As a** system administrator  
**I want to** use Yahoo Finance for Indian stocks  
**So that** I don't have API quota limitations

**Acceptance Criteria:**
- Indian stock API calls do NOT count toward TwelveData quota
- System uses Yahoo Finance (yfinance) which is free and unlimited
- No API key configuration required
- No caching needed (fast enough for real-time use)
- System displays "Using Yahoo Finance" in UI for transparency

## Technical Requirements

### TR-1: Backend Changes

#### 1.1 Market Type Support
- Add "indian_stocks" as valid market_type in `ZoneSearchRequest`
- Update `search_zones()` endpoint to handle indian_stocks market type
- Format symbols: append `.NS` suffix if not present (e.g., RELIANCE → RELIANCE.NS)
- Support both NSE and BSE exchanges (.NS for NSE, .BO for BSE)

#### 1.2 Price Fetching
- Update `get_mark_price()` endpoint to handle .NS/.BO suffixes
- Use Yahoo Finance (yfinance) for Indian stock prices
- No API key required, no quota limits
- No caching needed (fast enough for real-time use)
- Return prices as float (no currency conversion needed)

#### 1.3 Zone Computation
- Create new `compute_zones_indian_stocks()` function using yfinance
- Reuse logic from existing `yahoo_levels_finder.py`
- Indian stocks use similar thresholds to crypto (2-5% daily moves)
- V3 thresholds: 1d=8%, 1w=10%, 1M=15%
- V4 thresholds: 1d=1.5%, 1w=2%, 1M=5%

#### 1.4 MongoDB Storage
- Store market_type="indian_stocks" in scrip documents
- Preserve market_type when updating existing scrips
- Use market_type to determine price API in monitoring

### TR-2: Frontend Changes

#### 2.1 Market Type Dropdown
- Add "🇮🇳 Indian Stocks (NSE/BSE)" option to market type dropdown in ZoneFinder
- Position after "Forex (Gold/Currency)" option
- Update grid layout if needed to accommodate new option

#### 2.2 Symbol Input
- Accept Indian stock symbols without .NS/.BO suffix
- Show helper text: "Enter symbol (e.g., RELIANCE, TCS, INFY)"
- Backend automatically appends .NS suffix for NSE (default)
- User can explicitly use .BO for BSE stocks

#### 2.3 Results Display
- Display prices with ₹ symbol for Indian stocks
- Show "NSE" or "BSE" badge next to symbol
- Format prices to 2 decimal places

#### 2.4 Monitor Dashboard
- Display Indian stock prices with ₹ symbol
- Show market type badge (NSE/BSE)
- Use Yahoo Finance (yfinance) for price updates
- Show "Yahoo Finance" data source badge

### TR-3: Testing Requirements

#### 3.1 Test Script
- Update `test_reliance_indian_stock.py` to use Yahoo Finance
- Test RELIANCE.NS with V3 and V4 algorithms
- Test multiple timeframes: 1d, 1w, 1M
- Compare V3 vs V4 results
- Document expected behavior

#### 3.2 Integration Testing
- Test full flow: search → push → monitor
- Verify Yahoo Finance integration
- Test with multiple Indian stocks (RELIANCE, TCS, INFY, HDFCBANK, ITC)
- Verify no API quota issues

#### 3.3 Edge Cases
- Symbol not found on Yahoo Finance
- Invalid symbol format
- BSE vs NSE symbol handling (.BO vs .NS)
- Network errors and timeouts

### TR-4: Documentation

#### 4.1 User Documentation
- Create `INDIAN_STOCKS_GUIDE.md`
- List popular Indian stocks with Yahoo Finance symbols
- Explain NSE (.NS) vs BSE (.BO)
- Document V3 vs V4 algorithm selection
- Show example searches
- Explain Yahoo Finance as data source

#### 4.2 Technical Documentation
- Document Yahoo Finance (yfinance) integration
- Document symbol format requirements (.NS for NSE, .BO for BSE)
- Document why TwelveData is not used (requires paid plan)
- Update main README.md

## API Integration Details

### ⚠️ CRITICAL FINDING: TwelveData Requires Paid Plan for Indian Stocks

**Discovery:** TwelveData's free "Basic" plan does NOT support Indian stocks (NSE/BSE). Indian stocks require the "Grow" plan ($79/month).

**Test Results:**
- Symbol lookup works: `RELIANCE` on exchange `NSE` is found
- Time series data fails: Returns error "This symbol is available starting with Grow plan"
- Free plan only supports: US stocks, major forex pairs, major cryptocurrencies

### Alternative Free APIs for Indian Stocks

#### Option 1: Yahoo Finance (yfinance) - RECOMMENDED
- **Library:** `yfinance` (Python)
- **Symbol Format:** `RELIANCE.NS` for NSE, `RELIANCE.BO` for BSE
- **Cost:** FREE, unlimited
- **Data:** Historical OHLCV data, real-time quotes
- **Intervals:** 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
- **Limitations:** Rate limiting (not documented), occasional data gaps
- **Already Used:** Project already has `yahoo_levels_finder.py` using yfinance

#### Option 2: NSE India Official API
- **Endpoint:** `https://www.nseindia.com/api/`
- **Cost:** FREE
- **Data:** Real-time quotes, historical data
- **Limitations:** Requires headers to bypass bot detection, no official documentation
- **Complexity:** Medium (requires session management)

#### Option 3: Alpha Vantage
- **Endpoint:** `https://www.alphavantage.co/query`
- **Symbol Format:** `RELIANCE.BSE` (BSE only, no NSE)
- **Cost:** FREE (500 calls/day)
- **Limitations:** Only BSE stocks, not NSE

### Recommended Approach: Use Yahoo Finance (yfinance)

**Rationale:**
1. Already integrated in project (`yahoo_levels_finder.py`)
2. Completely free with no API key required
3. Supports both NSE (.NS) and BSE (.BO)
4. Good data quality and coverage
5. Simple Python library, no HTTP requests needed
6. Supports all required timeframes

**Implementation:**
- Reuse existing `yahoo_levels_finder.py` logic
- Symbol format: `RELIANCE.NS` for NSE, `RELIANCE.BO` for BSE
- No API quota tracking needed (free unlimited)
- No caching needed (fast enough for real-time use)

### Popular Indian Stocks
| Symbol | Company | Exchange | Yahoo Symbol |
|--------|---------|----------|--------------|
| RELIANCE | Reliance Industries | NSE | RELIANCE.NS |
| TCS | Tata Consultancy Services | NSE | TCS.NS |
| INFY | Infosys | NSE | INFY.NS |
| HDFCBANK | HDFC Bank | NSE | HDFCBANK.NS |
| ITC | ITC Limited | NSE | ITC.NS |
| HINDUNILVR | Hindustan Unilever | NSE | HINDUNILVR.NS |
| ICICIBANK | ICICI Bank | NSE | ICICIBANK.NS |
| SBIN | State Bank of India | NSE | SBIN.NS |
| BHARTIARTL | Bharti Airtel | NSE | BHARTIARTL.NS |
| KOTAKBANK | Kotak Mahindra Bank | NSE | KOTAKBANK.NS |

## Implementation Plan

### Phase 1: Backend Foundation (30 min)
1. Create `compute_zones_indian_stocks()` function using yfinance
2. Reuse logic from `yahoo_levels_finder.py`
3. Update `ZoneSearchRequest` model to accept indian_stocks
4. Update `search_zones()` to handle indian_stocks market type
5. Add symbol formatting logic (.NS suffix for NSE)
6. Update `get_mark_price()` for Indian stocks using yfinance
7. Update test script to use Yahoo Finance
8. Test with `python test_reliance_indian_stock.py`

### Phase 2: Frontend Integration (20 min)
1. Add Indian Stocks option to market type dropdown
2. Update symbol input placeholder/helper text
3. Add ₹ symbol formatting for prices
4. Add NSE/BSE badge display
5. Test search flow in browser

### Phase 3: Monitor Dashboard (15 min)
1. Update Monitor component to handle indian_stocks
2. Add ₹ symbol to price display
3. Add "Yahoo Finance" data source badge
4. Test price fetching
5. Verify alert triggering

### Phase 4: Testing & Documentation (25 min)
1. Run comprehensive tests with multiple stocks
2. Verify Yahoo Finance integration
3. Create INDIAN_STOCKS_GUIDE.md
4. Update main README.md
5. Document known limitations

**Total Estimated Time:** 90 minutes

## Success Criteria

### Functional
- ✅ User can search Indian stocks using NSE/BSE symbols
- ✅ System finds zones using V3/V4 algorithms
- ✅ User can monitor Indian stock levels
- ✅ Prices display in Indian Rupees (₹)
- ✅ No API quota limitations (Yahoo Finance is free)

### Technical
- ✅ Yahoo Finance (yfinance) integration works correctly
- ✅ Symbol formatting handles .NS/.BO suffixes
- ✅ MongoDB stores market_type correctly
- ✅ No breaking changes to existing crypto/forex functionality
- ✅ No API key configuration required

### Quality
- ✅ Test script validates functionality
- ✅ Documentation is complete and accurate
- ✅ Error handling for edge cases
- ✅ User-friendly error messages

## Risks & Mitigation

### Risk 1: Yahoo Finance Rate Limiting
**Impact:** Medium  
**Probability:** Low  
**Mitigation:** 
- Yahoo Finance has soft rate limits (not documented)
- Add retry logic with exponential backoff
- Show user-friendly error if rate limited
- Consider adding optional caching if issues arise

### Risk 2: Symbol Format Confusion
**Impact:** Medium  
**Probability:** Medium  
**Mitigation:**
- Auto-append .NS suffix in backend (NSE is default)
- Show clear helper text in UI
- Document symbol format in guide
- Handle both NSE (.NS) and BSE (.BO) formats

### Risk 3: Data Quality
**Impact:** Low  
**Probability:** Low  
**Mitigation:**
- Yahoo Finance is reliable for Indian stocks
- Test with popular stocks first
- Document which stocks are available
- Show clear error if symbol not found
- Provide list of verified symbols

### Risk 4: TwelveData Confusion
**Impact:** Low  
**Probability:** Medium  
**Mitigation:**
- Clearly document that Indian stocks use Yahoo Finance
- Show "Yahoo Finance" badge in UI
- Explain in documentation why TwelveData is not used
- Keep TwelveData for forex only

## Dependencies

### External
- Yahoo Finance (yfinance Python library) - FREE, no API key
- MongoDB (already configured)

### Internal
- `yahoo_levels_finder.py` logic (already exists)
- Zone computation algorithms (V3/V4)
- MongoDB storage mechanism

## Out of Scope

The following are explicitly NOT included in this spec:
- Real-time streaming prices for Indian stocks
- Intraday tick data below 1-minute intervals
- Order execution or trading functionality
- BSE-specific optimizations (NSE is primary focus)
- Currency conversion (prices stay in INR)
- Historical data beyond Yahoo Finance limits (~10 years)
- TwelveData integration for Indian stocks (requires paid plan)

## Notes

- Indian stocks typically move 2-5% daily, 5-10% weekly (similar to crypto)
- V4 algorithm may be better suited for Indian stocks due to lower thresholds
- NSE is the primary exchange; BSE support is secondary
- Yahoo Finance provides excellent coverage of major Indian stocks
- No API key or quota management needed (Yahoo Finance is free)
- TwelveData requires paid "Grow" plan ($79/month) for Indian stocks
- Consider adding more Indian exchanges (MCX, etc.) in future iterations
- yfinance library is already in requirements.txt
