"""
Test Backend API for Indian Stocks
Tests the /api/zones/search endpoint with Indian stocks
"""
import requests
import json

API_URL = "http://localhost:8000"

def test_search_indian_stock(symbol, timeframe="1d", version="v4"):
    """Test searching for Indian stock zones"""
    print(f"\n{'='*80}")
    print(f"Testing: {symbol} - {timeframe.upper()} - {version.upper()}")
    print(f"{'='*80}")
    
    try:
        response = requests.post(
            f"{API_URL}/api/zones/search",
            json={
                "symbol": symbol,
                "timeframe": timeframe,
                "market_type": "indian_stocks",
                "version": version
            },
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(f"Symbol: {data['symbol']}")
            print(f"Timeframe: {data['timeframe']}")
            print(f"Market Type: {data['market_type']}")
            print(f"Zones Found: {data['count']}")
            
            if data['zones']:
                print(f"\nTop 5 Zones:")
                for i, zone in enumerate(data['zones'][:5], 1):
                    print(f"  {i}. ₹{zone['top']:.2f} - ₹{zone['bottom']:.2f} | "
                          f"Rally={zone['rally_length']} Move={zone['total_move_pct']:.2f}% | "
                          f"Date={zone['date']}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Backend is not running!")
        print("\n💡 Please start the backend:")
        print("   cd crypto_levels_bhushan")
        print("   .\\restart_backend.bat")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_price(symbol):
    """Test getting current price for Indian stock"""
    print(f"\n{'='*80}")
    print(f"Testing Price API: {symbol}")
    print(f"{'='*80}")
    
    try:
        response = requests.get(
            f"{API_URL}/api/price/{symbol}",
            params={"market_type": "indian_stocks"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(f"Symbol: {data['symbol']}")
            print(f"Price: ₹{data['mark_price']:.2f}")
            print(f"Source: {data.get('source', 'N/A')}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Backend is not running!")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    print("\n" + "="*80)
    print("BACKEND API TEST - INDIAN STOCKS")
    print("="*80)
    print("\nTesting Indian Stocks support in backend API")
    print("API URL:", API_URL)
    print("="*80)
    
    # Test 1: Search zones for RELIANCE with V4
    success1 = test_search_indian_stock("RELIANCE", "1d", "v4")
    
    # Test 2: Search zones for TCS with V3
    success2 = test_search_indian_stock("TCS", "1w", "v3")
    
    # Test 3: Get current price for RELIANCE
    success3 = test_get_price("RELIANCE")
    
    # Test 4: Get current price for INFY
    success4 = test_get_price("INFY")
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"1. RELIANCE zones (V4, 1d): {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"2. TCS zones (V3, 1w): {'✅ PASS' if success2 else '❌ FAIL'}")
    print(f"3. RELIANCE price: {'✅ PASS' if success3 else '❌ FAIL'}")
    print(f"4. INFY price: {'✅ PASS' if success4 else '❌ FAIL'}")
    
    all_passed = success1 and success2 and success3 and success4
    
    if all_passed:
        print("\n🎉 All tests PASSED!")
        print("\n✅ Backend is ready for Indian Stocks!")
        print("\n🔄 Next Steps:")
        print("  1. Open frontend: http://localhost:3000")
        print("  2. Select 'Indian Stocks (NSE/BSE)' from Market Type")
        print("  3. Enter symbol: RELIANCE, TCS, or INFY")
        print("  4. Select V4 algorithm for better results")
        print("  5. Click 'Find Support Zones'")
    else:
        print("\n⚠️ Some tests FAILED!")
        print("\n💡 Troubleshooting:")
        print("  1. Make sure backend is running:")
        print("     cd crypto_levels_bhushan")
        print("     .\\restart_backend.bat")
        print("  2. Check backend logs for errors")
        print("  3. Verify yfinance is installed: pip install yfinance")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()

