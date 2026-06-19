import http.server
import socketserver
import json
import threading
import time
import platform
import subprocess
import socket
import hashlib
import os

PORT = 8080
TARGET_APP = "PowerPoint"
USERNAME = "admin"
PASSWORD = "church2025"
SESSIONS = set()

def generate_session_token():
    return hashlib.sha256(os.urandom(32)).hexdigest()

def check_auth(handler):
    cookie_header = handler.headers.get("Cookie", "")
    for part in cookie_header.split(";"):
        part = part.strip()
        if part.startswith("session="):
            token = part[8:]
            if token in SESSIONS:
                return True
    return False

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def focus_app():
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    EnumWindows = user32.EnumWindows
    GetWindowTextW = user32.GetWindowTextW
    SetForegroundWindow = user32.SetForegroundWindow
    ShowWindow = user32.ShowWindow
    IsIconic = user32.IsIconic
    IsWindowVisible = user32.IsWindowVisible
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    target_hwnd = None
    fallback_hwnd = None
    def enum_cb(hwnd, lParam):
        nonlocal target_hwnd, fallback_hwnd
        if not IsWindowVisible(hwnd):
            return True
        buf = ctypes.create_unicode_buffer(256)
        GetWindowTextW(hwnd, buf, 256)
        title = buf.value
        if TARGET_APP.lower() in title.lower():
            if "slide show" in title.lower() or "slideshow" in title.lower():
                target_hwnd = hwnd
                return False
            if fallback_hwnd is None:
                fallback_hwnd = hwnd
        return True
    EnumWindows(WNDENUMPROC(enum_cb), 0)
    if not target_hwnd:
        target_hwnd = fallback_hwnd
    if target_hwnd:
        if IsIconic(target_hwnd):
            ShowWindow(target_hwnd, 9)
        SetForegroundWindow(target_hwnd)
        time.sleep(0.05)

def press_key(key):
    global TARGET_APP
    if TARGET_APP != "__active__":
        focus_app()
    import ctypes
    VK_RIGHT = 0x27
    VK_LEFT = 0x25
    KEYEVENTF_KEYUP = 0x0002
    vk = VK_RIGHT if key == "right" else VK_LEFT
    ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
    ctypes.windll.user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)

LOGIN_PAGE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Slide Controller - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #1a1a2e;
            color: #eee;
            height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        h1 { font-size: 1.5rem; color: #a8d8ea; margin-bottom: 1.5rem; }
        .login-box {
            background: #2a2a4a;
            padding: 2rem;
            border-radius: 16px;
            min-width: 280px;
        }
        .login-box input {
            display: block;
            width: 100%;
            padding: 10px;
            margin-bottom: 1rem;
            border: 1px solid #444;
            border-radius: 8px;
            background: #1a1a2e;
            color: #eee;
            font-size: 1rem;
        }
        .login-box button {
            width: 100%;
            padding: 10px;
            border: none;
            border-radius: 8px;
            background: #00b4d8;
            color: white;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
        }
        .login-box button:active { transform: scale(0.97); }
        .error { color: #e94560; font-size: 0.85rem; margin-bottom: 1rem; display: none; }
    </style>
</head>
<body>
    <h1>&#9741; Slide Controller</h1>
    <div class="login-box">
        <p class="error" id="error">Invalid username or password</p>
        <input type="text" id="username" placeholder="Username" autocomplete="username">
        <input type="password" id="password" placeholder="Password" autocomplete="current-password">
        <button id="loginBtn">Login</button>
    </div>
    <script>
        function doLogin() {
            var user = document.getElementById("username").value;
            var pwd = document.getElementById("password").value;
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/login", true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        window.location.reload();
                    } else {
                        document.getElementById("error").style.display = "block";
                    }
                }
            };
            xhr.send(JSON.stringify({username: user, password: pwd}));
        }
        document.getElementById("loginBtn").addEventListener("click", doLogin);
        document.getElementById("password").addEventListener("keydown", function(e) {
            if (e.key === "Enter") doLogin();
        });
    </script>
</body>
</html>
'''

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Slide Controller</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #1a1a2e;
            color: #eee;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 1rem;
        }}
        h1 {{
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
            color: #a8d8ea;
        }}
        .info {{
            font-size: 0.8rem;
            color: #888;
            margin-bottom: 1.5rem;
            text-align: center;
        }}
        .info code {{
            background: #2a2a4a;
            padding: 2px 6px;
            border-radius: 4px;
            color: #a8d8ea;
        }}
        .target-section {{
            margin-bottom: 1.5rem;
            text-align: center;
            background: #2a2a4a;
            padding: 1rem;
            border-radius: 12px;
            max-width: 350px;
        }}
        .target-section h3 {{
            font-size: 0.85rem;
            color: #a8d8ea;
            margin-bottom: 0.8rem;
        }}
        .target-options {{
            display: flex;
            flex-direction: column;
            gap: 0.6rem;
            align-items: flex-start;
            padding-left: 1rem;
        }}
        .target-options label {{
            font-size: 0.85rem;
            color: #ccc;
            cursor: pointer;
        }}
        .target-options input[type="radio"] {{
            margin-right: 0.5rem;
        }}
        .custom-input {{
            width: 150px;
            padding: 4px 8px;
            border: 1px solid #444;
            border-radius: 6px;
            background: #1a1a2e;
            color: #eee;
            font-size: 0.85rem;
            margin-left: 0.5rem;
        }}
        .custom-input:disabled {{
            opacity: 0.4;
        }}
        .target-section .set-btn {{
            display: inline-block;
            margin-top: 0.8rem;
            padding: 6px 16px;
            border: none;
            border-radius: 8px;
            background: #4caf50;
            color: white;
            cursor: pointer;
            font-size: 0.85rem;
        }}
        .target-section .set-btn:active {{ transform: scale(0.95); }}
        .target-hint {{
            font-size: 0.7rem;
            color: #666;
            margin-top: 0.5rem;
            font-style: italic;
        }}
        .controls {{
            display: flex;
            gap: 2rem;
            align-items: center;
        }}
        .btn {{
            width: 140px;
            height: 140px;
            border: none;
            border-radius: 20px;
            font-size: 2.5rem;
            font-weight: bold;
            cursor: pointer;
            user-select: none;
            -webkit-tap-highlight-color: transparent;
            transition: transform 0.1s, box-shadow 0.1s;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
        }}
        .btn:active {{ transform: scale(0.92); }}
        .btn-prev {{
            background: #e94560;
            color: white;
            box-shadow: 0 6px 20px rgba(233, 69, 96, 0.4);
        }}
        .btn-next {{
            background: #00b4d8;
            color: white;
            box-shadow: 0 6px 20px rgba(0, 180, 216, 0.4);
        }}
        .btn span {{ font-size: 0.9rem; margin-top: 0.3rem; }}
        .status {{
            margin-top: 1.5rem;
            font-size: 0.9rem;
            color: #666;
            text-align: center;
        }}
        .status.ok {{ color: #4caf50; }}
        .instructions {{
            margin-top: 2rem;
            padding: 1rem;
            background: #2a2a4a;
            border-radius: 12px;
            max-width: 350px;
            font-size: 0.75rem;
            color: #aaa;
            line-height: 1.6;
        }}
        .instructions h3 {{
            color: #a8d8ea;
            margin-bottom: 0.5rem;
            font-size: 0.85rem;
        }}
        .instructions ol {{ padding-left: 1.2rem; }}
        @media (max-width: 400px) {{
            .btn {{ width: 120px; height: 120px; font-size: 2rem; }}
            .controls {{ gap: 1.5rem; }}
        }}
    </style>
</head>
<body>
    <h1>&#9741; Slide Controller</h1>
    <div class="info">
        Server IP: <code>{server_ip}:{port}</code>
    </div>

    <div class="target-section">
        <h3>Focus Mode</h3>
        <div class="target-options">
            <label><input type="radio" name="focusMode" value="powerpoint" checked> PowerPoint</label>
            <label><input type="radio" name="focusMode" value="custom"> Custom App:
                <input type="text" class="custom-input" id="customApp" placeholder="e.g. Word, Chrome" disabled>
            </label>
            <label><input type="radio" name="focusMode" value="active"> Active Window (no focus switch)</label>
        </div>
        <button class="set-btn" id="setAppBtn">Apply</button>
        <p class="target-hint">Custom: type any keyword from the window title (case-insensitive)</p>
    </div>

    <div class="controls">
        <button class="btn btn-prev" id="prevBtn">&#9664;<span>PREV</span></button>
        <button class="btn btn-next" id="nextBtn">&#9654;<span>NEXT</span></button>
    </div>
    <p class="status" id="status">Ready</p>

    <div class="instructions">
        <h3>How to Use</h3>
        <ol>
            <li>Run this server on the tech booth laptop</li>
            <li>Open the presentation app (PowerPoint, Google Slides, etc.)</li>
            <li>On the pastor's device, connect to the same Wi-Fi and open:<br>
                <code>http://{server_ip}:{port}</code></li>
            <li>Set the <b>Target App</b> name to match the window title (e.g., "PowerPoint", "Slides", "Impress")</li>
            <li>Tap PREV / NEXT to control slides</li>
        </ol>
    </div>

    <script>
        function sendCommand(action) {{
            var status = document.getElementById("status");
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/slide", true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.onreadystatechange = function() {{
                if (xhr.readyState === 4) {{
                    if (xhr.status === 200) {{
                        status.textContent = action.toUpperCase() + " sent";
                        status.className = "status ok";
                    }} else {{
                        status.textContent = "Error";
                        status.className = "status";
                    }}
                    setTimeout(function() {{
                        status.textContent = "Ready";
                        status.className = "status";
                    }}, 1500);
                }}
            }};
            xhr.send(JSON.stringify({{action: action}}));
        }}

        function setTargetApp() {{
            var radios = document.querySelectorAll('input[name="focusMode"]');
            var mode = "";
            for (var i = 0; i < radios.length; i++) {{
                if (radios[i].checked) {{ mode = radios[i].value; break; }}
            }}
            var appName = "";
            if (mode === "powerpoint") appName = "PowerPoint";
            else if (mode === "custom") appName = document.getElementById("customApp").value.trim();
            else if (mode === "active") appName = "__active__";
            if (mode === "custom" && !appName) {{
                document.getElementById("status").textContent = "Enter an app name";
                return;
            }}
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/target", true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.onreadystatechange = function() {{
                if (xhr.readyState === 4 && xhr.status === 200) {{
                    var status = document.getElementById("status");
                    var label = mode === "active" ? "Active Window" : appName;
                    status.textContent = "Mode: " + label;
                    status.className = "status ok";
                    setTimeout(function() {{
                        status.textContent = "Ready";
                        status.className = "status";
                    }}, 1500);
                }}
            }};
            xhr.send(JSON.stringify({{app: appName}}));
        }}

        var radios = document.querySelectorAll('input[name="focusMode"]');
        var customInput = document.getElementById("customApp");
        for (var i = 0; i < radios.length; i++) {{
            radios[i].addEventListener("change", function() {{
                customInput.disabled = (this.value !== "custom");
            }});
        }}

        document.getElementById("nextBtn").addEventListener("click", function() {{
            sendCommand("next");
        }});
        document.getElementById("prevBtn").addEventListener("click", function() {{
            sendCommand("prev");
        }});
        document.getElementById("setAppBtn").addEventListener("click", setTargetApp);

        document.addEventListener("keydown", function(e) {{
            if (e.target.tagName === "INPUT") return;
            if (e.key === "ArrowRight") sendCommand("next");
            if (e.key === "ArrowLeft") sendCommand("prev");
        }});
    </script>
</body>
</html>
"""

class SlideHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if not check_auth(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(LOGIN_PAGE.encode())
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        ip = get_local_ip()
        page = HTML_TEMPLATE.format(server_ip=ip, port=PORT, target_app=TARGET_APP)
        self.wfile.write(page.encode())

    def do_POST(self):
        global TARGET_APP
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        if self.path == "/api/login":
            try:
                data = json.loads(body)
                user = data.get("username", "")
                pwd = data.get("password", "")
                if user == USERNAME and pwd == PASSWORD:
                    token = generate_session_token()
                    SESSIONS.add(token)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Set-Cookie", f"session={token}; Path=/; HttpOnly")
                    self.end_headers()
                    self.wfile.write(json.dumps({"ok": True}).encode())
                else:
                    self.send_response(401)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Invalid credentials"}).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
            return
        if not check_auth(self):
            self.send_response(401)
            self.end_headers()
            return
        if self.path == "/api/slide":
            try:
                data = json.loads(body)
                action = data.get("action", "")
                if action == "next":
                    press_key("right")
                elif action == "prev":
                    press_key("left")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
        elif self.path == "/api/target":
            try:
                data = json.loads(body)
                TARGET_APP = data.get("app", "PowerPoint")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, "app": TARGET_APP}).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

def start_server():
    with socketserver.TCPServer(("", PORT), SlideHandler) as httpd:
        httpd.serve_forever()

def create_tray_icon():
    from pystray import Icon, MenuItem, Menu
    from PIL import Image, ImageDraw, ImageFont

    ip = get_local_ip()
    tooltip = f"Slide Controller\nhttp://{ip}:{PORT}\nUser: {USERNAME}"

    img = Image.new("RGB", (64, 64), "#1a1a2e")
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([4, 4, 60, 60], radius=10, fill="#00b4d8")
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except Exception:
        font = ImageFont.load_default()
    draw.text((15, 14), "SC", fill="white", font=font)

    def on_open_browser(icon, item):
        import webbrowser
        webbrowser.open(f"http://{ip}:{PORT}")

    def on_quit(icon, item):
        icon.stop()
        os._exit(0)

    menu = Menu(
        MenuItem(f"http://{ip}:{PORT}", on_open_browser),
        MenuItem(f"User: {USERNAME} / Pass: {PASSWORD}", None, enabled=False),
        MenuItem("Open in Browser", on_open_browser),
        MenuItem("Quit", on_quit),
    )

    icon = Icon("SlideController", img, tooltip, menu)
    icon.run()

def main():
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    ip = get_local_ip()
    print(f"Slide Controller running at http://{ip}:{PORT}")
    print("Running in system tray...")

    create_tray_icon()

if __name__ == "__main__":
    main()
