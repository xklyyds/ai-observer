import urllib.request
import urllib.error
import ssl
import json
from typing import Dict, Optional


def make_request(url: str, method: str = "GET", headers: Dict = None,
                 body: Dict = None, timeout: int = 10) -> Optional[dict]:
    headers = headers or {}
    headers.setdefault("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

    ctx = ssl.create_default_context()

    try:
        data = json.dumps(body).encode("utf-8") if body else None

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as response:
            content = response.read().decode("utf-8")

            if response.headers.get("content-type", "").lower().startswith("application/json"):
                return json.loads(content)
            return {"content": content}

    except urllib.error.HTTPError as e:
        return {"error": f"HTTP Error {e.code}: {e.reason}", "status_code": e.code}
    except urllib.error.URLError as e:
        return {"error": f"URL Error: {str(e)}"}
    except json.JSONDecodeError:
        return {"content": content} if "content" in locals() else {"error": "Invalid JSON response"}
    except Exception as e:
        return {"error": str(e)}

def setup_pythonanywhere_proxy():
    """Set global proxy for PythonAnywhere free accounts.
    Free accounts must route external HTTP through proxy.server:3128.
    Detects PA automatically - no config needed."""
    import os
    if os.path.exists('/home') and not os.environ.get('NO_PROXY'):
        try:
            proxy_handler = urllib.request.ProxyHandler({
                'http': 'http://proxy.server:3128',

            })
            opener = urllib.request.build_opener(proxy_handler)
            urllib.request.install_opener(opener)
            print("PythonAnywhere proxy configured")
        except Exception:
            pass


