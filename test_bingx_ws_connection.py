import asyncio
import websockets
import json
import gzip
import io

async def test_ws():
    url = "wss://open-api-swap.bingx.com/swap-market"
    print(f"Connecting to {url}...")
    
    async with websockets.connect(url) as ws:
        print("Connected!")
        
        # Subscribe to BTC-USDT 1m kline
        sub_msg = {
            "id": "test-id",
            "reqType": "sub",
            "dataType": "BTC-USDT@kline_1m"
        }
        await ws.send(json.dumps(sub_msg))
        print(f"Sent subscribe: {sub_msg}")
        
        for _ in range(5):
            msg = await ws.recv()
            
            # Try decompress
            try:
                decompressed = gzip.GzipFile(fileobj=io.BytesIO(msg)).read()
                text = decompressed.decode('utf-8')
            except Exception:
                text = msg
                
            print(f"Received: {text[:200]}...")
            
            if text == "Ping":
                await ws.send("Pong")
                print("Sent Pong")

if __name__ == "__main__":
    asyncio.run(test_ws())
