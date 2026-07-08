import urllib.request
import ssl
import json
from typing import Dict, Optional


def create_ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def make_request(url: str, method: str = "GET", headers: Dict = None, 
                 data: Dict = None, timeout: int = 10) -> Optional[dict]:
    headers = headers or {}
    headers.setdefault("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    
    ctx = create_ssl_context()
    
    try:
        if data:
            data = json.dumps(data).encode("utf-8")
        
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as response:
            content = response.read().decode("utf-8", errors="ignore")
            
            if response.headers.get("content-type", "").lower().startswith("application/json"):
                return json.loads(content)
            return {"content": content}
    
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP Error {e.code}: {e.reason}", "status_code": e.code}
    except urllib.error.URLError as e:
        return {"error": f"URL Error: {str(e)}"}
    except json.JSONDecodeError:
        return {"content": content} if 'content' in locals() else {"error": "Invalid JSON response"}
    except Exception as e:
        return {"error": str(e)}