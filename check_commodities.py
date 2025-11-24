from smarttrade.bingx_client import BingXClient
import logging
import json

logging.basicConfig(level=logging.INFO)

def check_commodities():
    client = BingXClient()
    try:
        contracts = client.swap_contracts()
        print(f"Total contracts found: {len(contracts)}")
        
        commodities_keywords = ["GOLD", "SILVER", "OIL", "CRUDE", "GAS", "CORN", "WHEAT", "SOY", "SUGAR", "COFFEE"]
        
        found = []
        for c in contracts:
            symbol = c.get("symbol", "")
            
            # Check symbol for XAU, XAG, WTI
            if "XAU" in symbol or "XAG" in symbol or "WTI" in symbol:
                 found.append(c)
                 continue

            # Check keywords
            for kw in commodities_keywords:
                if kw in symbol.upper():
                    found.append(c)
                    break
        
        print(f"Found {len(found)} potential commodities:")
        for f in found:
            print(f"{f.get('symbol')}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    check_commodities()
