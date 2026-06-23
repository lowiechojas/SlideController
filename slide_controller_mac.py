import http.server
import socketserver
import json
import threading
import time
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
    if TARGET_APP == "__active__":
        return
    script = f'tell application "{TARGET_APP}" to activate'
    subprocess.run(["osascript", "-e", script], capture_output=True)
    time.sleep(0.05)

def press_key(key):
    if TARGET_APP != "__active__":
        focus_app()
    keycode = "124" if key == "right" else "123"
    script = f'tell application "System Events" to key code {keycode}'
    subprocess.run(["osascript", "-e", script], capture_output=True)

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
            <label><input type="radio" name="focusMode" value="powerpoint" checked> Keynote / PowerPoint</label>
            <label><input type="radio" name="focusMode" value="custom"> Custom App:
                <input type="text" class="custom-input" id="customApp" placeholder="e.g. Keynote, Preview" disabled>
            </label>
            <label><input type="radio" name="focusMode" value="active"> Active Window (no focus switch)</label>
        </div>
        <button class="set-btn" id="setAppBtn">Apply</button>
        <p class="target-hint">Custom: type any app name exactly as shown in the Dock</p>
    </div>

    <div class="controls">
        <button class="btn btn-prev" id="prevBtn">&#9664;<span>PREV</span></button>
        <button class="btn btn-next" id="nextBtn">&#9654;<span>NEXT</span></button>
    </div>
    <p class="status" id="status">Ready</p>

    <div class="instructions">
        <h3>How to Use</h3>
        <ol>
            <li>Run this server on the tech booth Mac</li>
            <li>Open Keynote / PowerPoint and start the slideshow</li>
            <li>On the pastor's device, connect to the same Wi-Fi and open:<br>
                <code>http://{server_ip}:{port}</code></li>
            <li>Set the <b>Focus Mode</b> to match your presentation app</li>
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
                    print(f"[{time.strftime('%H:%M:%S')}] Login successful from {self.client_address[0]}")
                else:
                    self.send_response(401)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Invalid credentials"}).encode())
                    print(f"[{time.strftime('%H:%M:%S')}] Failed login attempt from {self.client_address[0]}")
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
                    print(f"[{time.strftime('%H:%M:%S')}] >> NEXT slide ({TARGET_APP})")
                elif action == "prev":
                    press_key("left")
                    print(f"[{time.strftime('%H:%M:%S')}] << PREV slide ({TARGET_APP})")
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
                print(f"[{time.strftime('%H:%M:%S')}] Target app changed to: {TARGET_APP}")
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

def create_menu_bar():
    import rumps

    ip = get_local_ip()

    class SlideControllerApp(rumps.App):
        def __init__(self):
            super().__init__("SC", title="⛪ SC")
            self.menu = [
                rumps.MenuItem(f"http://{ip}:{PORT}", callback=self.open_browser),
                rumps.MenuItem(f"User: {USERNAME} / Pass: {PASSWORD}"),
                None,
                rumps.MenuItem("Open in Browser", callback=self.open_browser),
            ]

        def open_browser(self, _):
            import webbrowser
            webbrowser.open(f"http://{ip}:{PORT}")

    SlideControllerApp().run()

def main():
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    ip = get_local_ip()
    print(f"Slide Controller running at http://{ip}:{PORT}")
    print("Running in macOS menu bar...")
    print(f"Login: {USERNAME} / {PASSWORD}")
    print("Press Ctrl+C to stop (or quit from menu bar icon).\n")

    try:
        create_menu_bar()
    except ImportError:
        print("'rumps' not installed. Running in terminal mode (no menu bar icon).")
        print("Install with: pip3 install rumps")
        print("Server is running. Press Ctrl+C to stop.\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopped.")

if __name__ == "__main__":
    main()
