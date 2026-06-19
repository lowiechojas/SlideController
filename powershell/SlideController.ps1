# Church Slide Controller - PowerShell Version
# Run: right-click > "Run with PowerShell" or use the .bat launcher

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# ============ CONFIGURATION ============
$Port = 8080
$Username = "admin"
$Password = "church2025"
$script:TargetApp = "PowerPoint"
$script:Sessions = @{}

# ============ HELPER FUNCTIONS ============

function Get-LocalIP {
    $ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" -and $_.PrefixOrigin -eq "Dhcp" } | Select-Object -First 1).IPAddress
    if (-not $ip) {
        $ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" -and $_.IPAddress -notlike "169.*" } | Select-Object -First 1).IPAddress
    }
    if (-not $ip) { $ip = "127.0.0.1" }
    return $ip
}

function New-SessionToken {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    return [System.BitConverter]::ToString($bytes).Replace("-","").ToLower()
}

function Test-Auth($request) {
    $cookie = $request.Headers["Cookie"]
    if ($cookie -match "session=([a-f0-9]+)") {
        $token = $Matches[1]
        return $script:Sessions.ContainsKey($token)
    }
    return $false
}

function Send-Key($key) {
    if ($script:TargetApp -ne "__active__") {
        Focus-TargetApp
    }
    Start-Sleep -Milliseconds 50
    $wshell = New-Object -ComObject WScript.Shell
    if ($key -eq "right") {
        $wshell.SendKeys("{RIGHT}")
    } else {
        $wshell.SendKeys("{LEFT}")
    }
}

function Focus-TargetApp {
    Add-Type @"
    using System;
    using System.Runtime.InteropServices;
    using System.Text;
    public class WinAPI {
        [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
        [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
        [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
        [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
        [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
        [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hWnd);
        public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    }
"@ -ErrorAction SilentlyContinue

    $targetHwnd = [IntPtr]::Zero
    $fallbackHwnd = [IntPtr]::Zero
    $target = $script:TargetApp.ToLower()

    $callback = [WinAPI+EnumWindowsProc]{
        param($hWnd, $lParam)
        if (-not [WinAPI]::IsWindowVisible($hWnd)) { return $true }
        $sb = New-Object System.Text.StringBuilder 256
        [WinAPI]::GetWindowText($hWnd, $sb, 256) | Out-Null
        $title = $sb.ToString().ToLower()
        if ($title.Contains($target)) {
            if ($title.Contains("slide show") -or $title.Contains("slideshow")) {
                $script:foundHwnd = $hWnd
                return $false
            }
            if ($script:fallbackFound -eq [IntPtr]::Zero) {
                $script:fallbackFound = $hWnd
            }
        }
        return $true
    }

    $script:foundHwnd = [IntPtr]::Zero
    $script:fallbackFound = [IntPtr]::Zero
    [WinAPI]::EnumWindows($callback, [IntPtr]::Zero) | Out-Null

    $hwnd = if ($script:foundHwnd -ne [IntPtr]::Zero) { $script:foundHwnd } else { $script:fallbackFound }
    if ($hwnd -ne [IntPtr]::Zero) {
        if ([WinAPI]::IsIconic($hwnd)) {
            [WinAPI]::ShowWindow($hwnd, 9) | Out-Null
        }
        [WinAPI]::SetForegroundWindow($hwnd) | Out-Null
    }
}

# ============ HTML PAGES ============

$LoginPage = @'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Slide Controller - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #1a1a2e; color: #eee; height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; }
        h1 { font-size: 1.5rem; color: #a8d8ea; margin-bottom: 1.5rem; }
        .login-box { background: #2a2a4a; padding: 2rem; border-radius: 16px; min-width: 280px; }
        .login-box input { display: block; width: 100%; padding: 10px; margin-bottom: 1rem; border: 1px solid #444; border-radius: 8px; background: #1a1a2e; color: #eee; font-size: 1rem; }
        .login-box button { width: 100%; padding: 10px; border: none; border-radius: 8px; background: #00b4d8; color: white; font-size: 1rem; font-weight: bold; cursor: pointer; }
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
                    if (xhr.status === 200) { window.location.reload(); }
                    else { document.getElementById("error").style.display = "block"; }
                }
            };
            xhr.send(JSON.stringify({username: user, password: pwd}));
        }
        document.getElementById("loginBtn").addEventListener("click", doLogin);
        document.getElementById("password").addEventListener("keydown", function(e) { if (e.key === "Enter") doLogin(); });
    </script>
</body>
</html>
'@

function Get-MainPage {
    $ip = Get-LocalIP
    return @"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Slide Controller</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #1a1a2e; color: #eee; min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 1rem; }
        h1 { font-size: 1.5rem; margin-bottom: 0.5rem; color: #a8d8ea; }
        .info { font-size: 0.8rem; color: #888; margin-bottom: 1.5rem; text-align: center; }
        .info code { background: #2a2a4a; padding: 2px 6px; border-radius: 4px; color: #a8d8ea; }
        .target-section { margin-bottom: 1.5rem; text-align: center; background: #2a2a4a; padding: 1rem; border-radius: 12px; max-width: 350px; }
        .target-section h3 { font-size: 0.85rem; color: #a8d8ea; margin-bottom: 0.8rem; }
        .target-options { display: flex; flex-direction: column; gap: 0.6rem; align-items: flex-start; padding-left: 1rem; }
        .target-options label { font-size: 0.85rem; color: #ccc; cursor: pointer; }
        .target-options input[type="radio"] { margin-right: 0.5rem; }
        .custom-input { width: 150px; padding: 4px 8px; border: 1px solid #444; border-radius: 6px; background: #1a1a2e; color: #eee; font-size: 0.85rem; margin-left: 0.5rem; }
        .custom-input:disabled { opacity: 0.4; }
        .target-section .set-btn { display: inline-block; margin-top: 0.8rem; padding: 6px 16px; border: none; border-radius: 8px; background: #4caf50; color: white; cursor: pointer; font-size: 0.85rem; }
        .target-section .set-btn:active { transform: scale(0.95); }
        .target-hint { font-size: 0.7rem; color: #666; margin-top: 0.5rem; font-style: italic; }
        .controls { display: flex; gap: 2rem; align-items: center; }
        .btn { width: 140px; height: 140px; border: none; border-radius: 20px; font-size: 2.5rem; font-weight: bold; cursor: pointer; user-select: none; -webkit-tap-highlight-color: transparent; transition: transform 0.1s, box-shadow 0.1s; display: flex; align-items: center; justify-content: center; flex-direction: column; }
        .btn:active { transform: scale(0.92); }
        .btn-prev { background: #e94560; color: white; box-shadow: 0 6px 20px rgba(233, 69, 96, 0.4); }
        .btn-next { background: #00b4d8; color: white; box-shadow: 0 6px 20px rgba(0, 180, 216, 0.4); }
        .btn span { font-size: 0.9rem; margin-top: 0.3rem; }
        .status { margin-top: 1.5rem; font-size: 0.9rem; color: #666; text-align: center; }
        .status.ok { color: #4caf50; }
        .instructions { margin-top: 2rem; padding: 1rem; background: #2a2a4a; border-radius: 12px; max-width: 350px; font-size: 0.75rem; color: #aaa; line-height: 1.6; }
        .instructions h3 { color: #a8d8ea; margin-bottom: 0.5rem; font-size: 0.85rem; }
        .instructions ol { padding-left: 1.2rem; }
        @media (max-width: 400px) { .btn { width: 120px; height: 120px; font-size: 2rem; } .controls { gap: 1.5rem; } }
    </style>
</head>
<body>
    <h1>&#9741; Slide Controller</h1>
    <div class="info">Server IP: <code>${ip}:${Port}</code></div>
    <div class="target-section">
        <h3>Focus Mode</h3>
        <div class="target-options">
            <label><input type="radio" name="focusMode" value="powerpoint" checked> PowerPoint</label>
            <label><input type="radio" name="focusMode" value="custom"> Custom App: <input type="text" class="custom-input" id="customApp" placeholder="e.g. Word, Chrome" disabled></label>
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
            <li>Open the presentation app</li>
            <li>On the pastor's device, connect to the same Wi-Fi and open:<br><code>http://${ip}:${Port}</code></li>
            <li>Set the Target App to match the window title</li>
            <li>Tap PREV / NEXT to control slides</li>
        </ol>
    </div>
    <script>
        function sendCommand(action) {
            var status = document.getElementById("status");
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/slide", true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) { status.textContent = action.toUpperCase() + " sent"; status.className = "status ok"; }
                    else { status.textContent = "Error"; status.className = "status"; }
                    setTimeout(function() { status.textContent = "Ready"; status.className = "status"; }, 1500);
                }
            };
            xhr.send(JSON.stringify({action: action}));
        }
        function setTargetApp() {
            var radios = document.querySelectorAll('input[name="focusMode"]');
            var mode = "";
            for (var i = 0; i < radios.length; i++) { if (radios[i].checked) { mode = radios[i].value; break; } }
            var appName = "";
            if (mode === "powerpoint") appName = "PowerPoint";
            else if (mode === "custom") appName = document.getElementById("customApp").value.trim();
            else if (mode === "active") appName = "__active__";
            if (mode === "custom" && !appName) { document.getElementById("status").textContent = "Enter an app name"; return; }
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/target", true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    var status = document.getElementById("status");
                    var label = mode === "active" ? "Active Window" : appName;
                    status.textContent = "Mode: " + label; status.className = "status ok";
                    setTimeout(function() { status.textContent = "Ready"; status.className = "status"; }, 1500);
                }
            };
            xhr.send(JSON.stringify({app: appName}));
        }
        var radios = document.querySelectorAll('input[name="focusMode"]');
        var customInput = document.getElementById("customApp");
        for (var i = 0; i < radios.length; i++) { radios[i].addEventListener("change", function() { customInput.disabled = (this.value !== "custom"); }); }
        document.getElementById("nextBtn").addEventListener("click", function() { sendCommand("next"); });
        document.getElementById("prevBtn").addEventListener("click", function() { sendCommand("prev"); });
        document.getElementById("setAppBtn").addEventListener("click", setTargetApp);
        document.addEventListener("keydown", function(e) { if (e.target.tagName === "INPUT") return; if (e.key === "ArrowRight") sendCommand("next"); if (e.key === "ArrowLeft") sendCommand("prev"); });
    </script>
</body>
</html>
"@
}

# ============ HTTP SERVER ============

function Start-SlideServer {
    $ip = Get-LocalIP
    $prefix = "http://+:$Port/"

    # Create HTTP listener
    $listener = New-Object System.Net.HttpListener
    $listener.Prefixes.Add($prefix)

    try {
        $listener.Start()
    } catch {
        Write-Host "ERROR: Could not start listener. Try running as Administrator." -ForegroundColor Red
        Write-Host "Or run: netsh http add urlacl url=http://+:$Port/ user=$env:USERNAME"
        pause
        return
    }

    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  SLIDE CONTROLLER SERVER (PowerShell)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  URL: http://${ip}:${Port}" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Login: $Username / $Password"
    Write-Host ""
    Write-Host "  Press Ctrl+C to stop."
    Write-Host "========================================" -ForegroundColor Cyan

    while ($listener.IsListening) {
        try {
            $context = $listener.GetContext()
        } catch {
            break
        }
        $request = $context.Request
        $response = $context.Response

        $path = $request.Url.AbsolutePath
        $method = $request.HttpMethod

        if ($method -eq "GET" -and $path -eq "/") {
            if (Test-Auth $request) {
                $html = Get-MainPage
            } else {
                $html = $LoginPage
            }
            $buffer = [System.Text.Encoding]::UTF8.GetBytes($html)
            $response.ContentType = "text/html; charset=utf-8"
            $response.ContentLength64 = $buffer.Length
            $response.OutputStream.Write($buffer, 0, $buffer.Length)
        }
        elseif ($method -eq "POST") {
            $reader = New-Object System.IO.StreamReader($request.InputStream)
            $body = $reader.ReadToEnd()
            $reader.Close()

            if ($path -eq "/api/login") {
                $data = $body | ConvertFrom-Json
                if ($data.username -eq $Username -and $data.password -eq $Password) {
                    $token = New-SessionToken
                    $script:Sessions[$token] = $true
                    $response.Headers.Add("Set-Cookie", "session=$token; Path=/; HttpOnly")
                    $json = '{"ok":true}'
                    $response.StatusCode = 200
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Login OK from $($request.RemoteEndPoint)" -ForegroundColor Green
                } else {
                    $json = '{"error":"Invalid credentials"}'
                    $response.StatusCode = 401
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Failed login from $($request.RemoteEndPoint)" -ForegroundColor Red
                }
                $buffer = [System.Text.Encoding]::UTF8.GetBytes($json)
                $response.ContentType = "application/json"
                $response.ContentLength64 = $buffer.Length
                $response.OutputStream.Write($buffer, 0, $buffer.Length)
            }
            elseif (-not (Test-Auth $request)) {
                $response.StatusCode = 401
                $response.ContentLength64 = 0
            }
            elseif ($path -eq "/api/slide") {
                $data = $body | ConvertFrom-Json
                if ($data.action -eq "next") {
                    Send-Key "right"
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] >> NEXT ($($script:TargetApp))" -ForegroundColor Yellow
                } elseif ($data.action -eq "prev") {
                    Send-Key "left"
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] << PREV ($($script:TargetApp))" -ForegroundColor Yellow
                }
                $json = '{"ok":true}'
                $buffer = [System.Text.Encoding]::UTF8.GetBytes($json)
                $response.ContentType = "application/json"
                $response.ContentLength64 = $buffer.Length
                $response.OutputStream.Write($buffer, 0, $buffer.Length)
            }
            elseif ($path -eq "/api/target") {
                $data = $body | ConvertFrom-Json
                $script:TargetApp = $data.app
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Target changed to: $($script:TargetApp)" -ForegroundColor Magenta
                $json = "{`"ok`":true,`"app`":`"$($script:TargetApp)`"}"
                $buffer = [System.Text.Encoding]::UTF8.GetBytes($json)
                $response.ContentType = "application/json"
                $response.ContentLength64 = $buffer.Length
                $response.OutputStream.Write($buffer, 0, $buffer.Length)
            }
            else {
                $response.StatusCode = 404
                $response.ContentLength64 = 0
            }
        }
        else {
            $response.StatusCode = 404
            $response.ContentLength64 = 0
        }

        $response.Close()
    }

    $listener.Stop()
}

# ============ SYSTEM TRAY ============

function Start-WithTray {
    $ip = Get-LocalIP

    # Hide console window
    Add-Type @"
    using System;
    using System.Runtime.InteropServices;
    public class ConsoleWindow {
        [DllImport("kernel32.dll")] public static extern IntPtr GetConsoleWindow();
        [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    }
"@ -ErrorAction SilentlyContinue
    $consoleHwnd = [ConsoleWindow]::GetConsoleWindow()
    [ConsoleWindow]::ShowWindow($consoleHwnd, 0) | Out-Null

    # Create notify icon
    $notifyIcon = New-Object System.Windows.Forms.NotifyIcon
    $notifyIcon.Text = "Slide Controller`nhttp://${ip}:${Port}`nUser: ${Username}"
    $notifyIcon.Visible = $true

    # Create a simple icon
    $bmp = New-Object System.Drawing.Bitmap(32, 32)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.Clear([System.Drawing.Color]::FromArgb(0, 180, 216))
    $font = New-Object System.Drawing.Font("Arial", 12, [System.Drawing.FontStyle]::Bold)
    $g.DrawString("SC", $font, [System.Drawing.Brushes]::White, 2, 6)
    $g.Dispose()
    $notifyIcon.Icon = [System.Drawing.Icon]::FromHandle($bmp.GetHicon())

    # Context menu
    $menu = New-Object System.Windows.Forms.ContextMenuStrip
    $urlItem = $menu.Items.Add("http://${ip}:${Port}")
    $urlItem.Add_Click({ Start-Process "http://${ip}:${Port}" })
    $credsItem = $menu.Items.Add("User: ${Username} / Pass: ${Password}")
    $credsItem.Enabled = $false
    $menu.Items.Add("-")
    $openItem = $menu.Items.Add("Open in Browser")
    $openItem.Add_Click({ Start-Process "http://${ip}:${Port}" })
    $quitItem = $menu.Items.Add("Quit")
    $quitItem.Add_Click({
        $notifyIcon.Visible = $false
        $notifyIcon.Dispose()
        [System.Windows.Forms.Application]::Exit()
        [Environment]::Exit(0)
    })
    $notifyIcon.ContextMenuStrip = $menu

    # Double-click opens browser
    $notifyIcon.Add_DoubleClick({ Start-Process "http://${ip}:${Port}" })

    # Start server in background
    $serverJob = Start-Job -ScriptBlock {
        param($scriptPath)
        . $scriptPath
        Start-SlideServer
    } -ArgumentList $MyInvocation.MyCommand.Path

    # Run message loop
    [System.Windows.Forms.Application]::Run()
}

# ============ MAIN ============

$mode = if ($args -contains "-tray") { "tray" } else { "console" }

if ($mode -eq "tray") {
    Start-WithTray
} else {
    Start-SlideServer
}
