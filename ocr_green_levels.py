"""
Simple OCR - Just extract all green text from margins
"""
import os
import json
import re
import cv2
import numpy as np
import easyocr
from datetime import datetime

def extract_levels_simple(image_path):
    """Simple approach: OCR entire left/right margins"""
    print(f"\nAnalyzing: {os.path.basename(image_path)}")
    
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img is None:
        print("   ERROR: Cannot read image")
        return []
    
    height, width = img.shape[:2]
    print(f"   Size: {width}x{height}")
    
    # Extract left margin only (right side has price axis noise)
    left_margin = img[150:height-150, 0:300]
    
    # Save margin for OCR
    cv2.imwrite('temp_left.png', left_margin)
    
    # Initialize OCR
    reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    
    all_numbers = set()
    
    # OCR on left margin only
    try:
        results = reader.readtext('temp_left.png', detail=1)
        for (bbox, text, conf) in results:
            if conf > 0.5:
                # Extract numbers with decimals
                numbers = re.findall(r'(\d{3,5}\.\d{1,2})', text.replace(',', ''))
                for num_str in numbers:
                    try:
                        num = float(num_str)
                        if 100 < num < 100000:
                            all_numbers.add(num)
                            print(f"   Found: {num} ('{text}', conf: {conf:.2f})")
                    except:
                        pass
    except Exception as e:
        print(f"   Error: {e}")
    
    # Cleanup
    if os.path.exists('temp_left.png'):
        os.remove('temp_left.png')
    
    levels = sorted(all_numbers, reverse=True)
    print(f"   Found {len(levels)} unique levels: {levels}")
    
    return levels

def main():
    print("="*70)
    print("   Simple Green Level OCR")
    print("="*70)
    
    screenshot_dir = 'tradingview_screenshots'
    
    if not os.path.exists(screenshot_dir):
        print(f"ERROR: Directory not found: {screenshot_dir}")
        return
    
    screenshots = sorted([f for f in os.listdir(screenshot_dir) if f.endswith('.png')])
    
    if not screenshots:
        print(f"ERROR: No screenshots found")
        return
    
    print(f"\nFound {len(screenshots)} screenshots\n")
    
    results = []
    
    for i, screenshot in enumerate(screenshots, 1):
        print(f"[{i}/{len(screenshots)}]")
        
        symbol = screenshot.replace('_NSE.png', '')
        image_path = os.path.join(screenshot_dir, screenshot).replace('\\', '/')
        
        support_levels = extract_levels_simple(image_path)
        
        if support_levels:
            result = {
                'symbol': symbol,
                'exchange': 'NSE',
                'market_type': 'indian_stock',
                'support_levels': support_levels,
                'resistance_levels': [],
                'screenshot': image_path,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'TradingView Simple OCR',
                'success': True
            }
        else:
            result = {
                'symbol': symbol,
                'screenshot': image_path,
                'success': False,
                'error': 'No levels detected'
            }
        
        results.append(result)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'tradingview_levels_{timestamp}.json'
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Summary
    print("\n" + "="*70)
    print("COMPLETE")
    print("="*70)
    
    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]
    
    print(f"\nSuccessful: {len(successful)}/{len(results)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        print(f"\nExtracted Levels:")
        for r in successful:
            print(f"   {r['symbol']:15} - {len(r['support_levels'])} levels")
    
    if failed:
        print(f"\nFailed: {', '.join([r['symbol'] for r in failed])}")
    
    print(f"\nResults saved to: {output_file}")
    
    return output_file

if __name__ == "__main__":
    main()
