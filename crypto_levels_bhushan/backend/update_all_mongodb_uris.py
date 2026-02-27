"""
Update MongoDB URI in all Python files
"""
import os
import glob

OLD_URI = "mongodb+srv://bhushanstonks_db_user:61qQn4sCqnosMmuB@deltapricetracker.zzpfett.mongodb.net/?appName=DeltaPriceTracker"
NEW_URI = "mongodb+srv://bhushanstonks_db_user:61qQn4sCqnosMmuB@deltapricetracker.zzpfett.mongodb.net/?appName=DeltaPriceTracker"

print("="*70)
print("Updating MongoDB URI in all Python files")
print("="*70)

# Find all Python files
python_files = []
for root, dirs, files in os.walk('.'):
    # Skip venv and __pycache__
    dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', 'node_modules', '.git']]
    for file in files:
        if file.endswith('.py'):
            python_files.append(os.path.join(root, file))

# Also check parent directory
for root, dirs, files in os.walk('..'):
    dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', 'node_modules', '.git', 'frontend', 'tradingview_screenshots']]
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            if filepath not in python_files:
                python_files.append(filepath)

print(f"\nFound {len(python_files)} Python files")

updated_files = []
for filepath in python_files:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if OLD_URI in content:
            new_content = content.replace(OLD_URI, NEW_URI)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            updated_files.append(filepath)
            print(f"✅ Updated: {filepath}")
    except Exception as e:
        print(f"⚠️ Error updating {filepath}: {e}")

print("\n" + "="*70)
print(f"✅ Updated {len(updated_files)} files")
print("="*70)

if updated_files:
    print("\nUpdated files:")
    for f in updated_files:
        print(f"  - {f}")

print("\n✅ All MongoDB URIs updated!")
print("\nNext step: Restart backend")
print("  python main.py")
