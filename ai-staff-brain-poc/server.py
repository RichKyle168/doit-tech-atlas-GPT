from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode, urlsplit, parse_qs
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import base64
import hmac
import html
import json
import os
import secrets
import time

ROOT = Path(__file__).resolve().parent
USER = os.environ.get("POC_USERNAME", "poc")
PASSWORD = os.environ.get("POC_PASSWORD", "")
CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
FOLDER_ID = os.environ.get("GOOGLE_FOLDER_ID", "1hALygoKf7dROPJpbDCwe6UrzcJH4RvTL")
REDIRECT_URI = os.environ.get(
    "GOOGLE_REDIRECT_URI",
    "https://ai-staff-brain-poc.onrender.com/auth/google/callback"
)
SCOPES = "https://www.googleapis.com/auth/drive.metadata.readonly"
STATES = {}

def page(title, body):
    return ("""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>""" + html.escape(title) + """</title>
<style>body{font-family:system-ui,"Noto Sans TC",sans-serif;background:#f4f8fb;color:#18384e;margin:0}
main{max-width:850px;margin:36px auto;background:white;padding:30px;border-radius:17px;box-shadow:0 7px 30px #15375113}
h1{color:#103b66}a.button{display:inline-block;padding:10px 20px;background:#136cba;color:white;text-decoration:none;border-radius:9px}
table{border-collapse:collapse;width:100%}th,td{padding:11px 7px;border-bottom:1px solid #e4eaf0;text-align:left}
small,p{line-height:1.6;color:#536779}code{overflow-wrap:anywhere}th{font-size:13px;color:#637b91}</style>
</head><body><main><p><a href="/">← 回 AI幕僚大腦</a></p>""" + body + "</main></body></html>").encode("utf-8")

class Handler(BaseHTTPRequestHandler):
    def respond(self, status, data=b"", mime="text/plain; charset=utf-8", extra=None):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
        if extra:
            for k,v in extra.items(): self.send_header(k,v)
        self.end_headers()
        if self.command != "HEAD": self.wfile.write(data)

    def html(self, status, title, body):
        self.respond(status, page(title,body), "text/html; charset=utf-8")

    def redirect(self, url, cookie=None):
        headers = {"Location":url}
        if cookie: headers["Set-Cookie"] = cookie
        self.respond(302,b"",extra=headers)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/health":
            return self.respond(200,b"ok")
        if not PASSWORD:
            return self.respond(503,b"POC authentication not configured.")
        expected = "Basic " + base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()
        if not hmac.compare_digest(self.headers.get("Authorization",""),expected):
            return self.respond(401,"請使用測試帳號登入。".encode("utf-8"),
                                extra={"WWW-Authenticate":'Basic realm="AI Staff Brain Demo", charset="UTF-8"'})
        if path == "/robots.txt":
            return self.respond(200,b"User-agent: *\nDisallow: /\n")
        if path == "/drive-test":
            if not (CLIENT_ID and CLIENT_SECRET):
                return self.html(200,"Google Drive 連線測試","""
<h1>Google Drive 連線測試</h1>
<p>網站的 Google OAuth 尚未設定，無法從 Render 自動取得你的 Google Drive 授權。</p>
<p>請先在 Google Cloud 建立 OAuth「網頁應用程式」用戶端、啟用 Google Drive API，
將測試帳號加入 OAuth 測試使用者，並將 Client ID / Client Secret 存入 Render 的環境變數。</p>
<p>授權回呼網址：<code>""" + html.escape(REDIRECT_URI) + """</code></p>
<p>這項測試只要求 Google Drive 檔案中繼資料的唯讀權限，不會讀取文件內容或保存存取權杖。</p>""")
            return self.html(200,"Google Drive 連線測試",
                "<h1>Google Drive 連線測試</h1><p>僅讀取指定資料夾第一層的檔名、類型與修改日期；不讀取或修改內容。</p>"
                '<p><a class="button" href="/auth/google/start">使用 Google 帳號授權並讀取清單</a></p>'
                "<small>授權時請選擇能存取該資料夾的 Google 帳號。授權僅供單次測試。</small>")
        if path == "/auth/google/start":
            if not (CLIENT_ID and CLIENT_SECRET):
                return self.redirect("/drive-test")
            now = time.time()
            for k,t in list(STATES.items()):
                if t < now-600: del STATES[k]
            state = secrets.token_urlsafe(32)
            STATES[state] = now
            params = urlencode({
                "client_id": CLIENT_ID,
                "redirect_uri": REDIRECT_URI,
                "response_type": "code",
                "scope": SCOPES,
                "state": state,
                "access_type": "online",
                "prompt": "consent"
            })
            cookie = f"gd_auth_state={state}; Max-Age=600; Path=/auth/google; Secure; HttpOnly; SameSite=Lax"
            return self.redirect("https://accounts.google.com/o/oauth2/v2/auth?"+params,cookie=cookie)
        if path == "/auth/google/callback":
            return self.handle_callback()
        if path in ("/","/index.html"):
            return self.respond(200,(ROOT/"index.html").read_bytes(),"text/html; charset=utf-8")
        return self.respond(404,b"Not found")

    def handle_callback(self):
        q = parse_qs(urlsplit(self.path).query)
        if q.get("error"):
            return self.html(400,"Google 授權未完成","<h1>Google 授權未完成</h1><p>請返回後重新嘗試，或檢查 Google OAuth 設定。</p>")
        state = q.get("state",[""])[0]
        cookie_state = ""
        for part in self.headers.get("Cookie","").split(";"):
            part = part.strip()
            if part.startswith("gd_auth_state="):
                cookie_state = part.split("=",1)[1]
        original = STATES.pop(state,None)
        if not state or not cookie_state or not hmac.compare_digest(state,cookie_state) or original is None or time.time()-original>600:
            return self.html(400,"授權狀態過期","<h1>授權狀態過期或不相符</h1><p>請返回測試頁重新授權。</p>")
        code = q.get("code",[""])[0]
        if not code:
            return self.html(400,"授權缺少資訊","<h1>未收到 Google 授權碼</h1>")
        try:
            payload = urlencode({
                "code": code, "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI, "grant_type": "authorization_code"
            }).encode()
            req = Request("https://oauth2.googleapis.com/token",data=payload,
                          headers={"Content-Type":"application/x-www-form-urlencoded"})
            with urlopen(req,timeout=12) as rsp:
                token = json.load(rsp).get("access_token")
            if not token: raise ValueError("Google did not return an access token")
            query = urlencode({
                "q": f"'{FOLDER_ID}' in parents and trashed = false",
                "fields": "nextPageToken,files(id,name,mimeType,modifiedTime,webViewLink)",
                "pageSize": "100"
            })
            req = Request("https://www.googleapis.com/drive/v3/files?"+query,
                          headers={"Authorization":f"Bearer {token}"})
            with urlopen(req,timeout=12) as rsp:
                response = json.load(rsp)
            rows = response.get("files",[])
            html_rows = ""
            for f in rows:
                n=html.escape(f.get("name",""))
                mt=html.escape(f.get("mimeType",""))
                md=html.escape(f.get("modifiedTime","")[:10])
                html_rows += f"<tr><td>{n}</td><td>{mt}</td><td>{md}</td></tr>"
            body = (f"<h1>Google Drive 讀取成功</h1><p>指定資料夾第一層共讀取 <b>{len(rows)}</b> 筆檔案／資料夾中繼資料。</p>"
                    "<table><thead><tr><th>名稱</th><th>類型</th><th>修改日期</th></tr></thead><tbody>"+
                    html_rows+"</tbody></table><p><small>本次權杖未保存，未讀取任何文件本文。</small></p>")
            if response.get("nextPageToken"):
                body += "<p>本頁只顯示前100筆。</p>"
            return self.html(200,"Google Drive 讀取成功",body)
        except (HTTPError,ValueError,TimeoutError,OSError) as exc:
            status = getattr(exc,"code",500)
            # Do not include tokens, response bodies or Google credentials in errors.
            return self.html(502,"Google Drive 測試失敗",
                "<h1>Google Drive 測試未完成</h1><p>請確認 Google Drive API、OAuth 測試使用者、帳號權限以及回呼網址。</p>"
                f"<p>上游狀態代碼：{html.escape(str(status))}</p>")
        except Exception:
            return self.html(500,"伺服器錯誤","<h1>測試未完成</h1><p>請檢查網站部署設定。</p>")

if __name__ == "__main__":
    port = int(os.environ.get("PORT","8080"))
    print(f"AI Staff Brain demo listening on port {port}",flush=True)
    ThreadingHTTPServer(("0.0.0.0",port),Handler).serve_forever()
