/**
 * customer.js - Customer Smartphone Simulator Logic
 * Handles client-side offline mode toggle, TOTP QR generation with 60s countdown,
 * Apple Pay NFC simulation, and in-store Wi-Fi onboarding.
 */

let isOnline = false; // Default to Offline (Subway/Basement Supermarket) to showcase the problem immediately
let preloadedTokens = [];
let activeToken = null;
let currentQrPayload = null;
let lastUsedPayload = null;
let countdownSeconds = 60;
let qrCodeInstance = null;
let timerInterval = null;

document.addEventListener("DOMContentLoaded", () => {
  initCustomerSimulator();
});

async function initCustomerSimulator() {
  await loadCustomerStatus();
  await prefetchTokens();
  setupNetworkSwitch();
  startTotpCycle();
}

async function loadCustomerStatus() {
  try {
    const res = await fetch("/api/v1/customer");
    const data = await res.json();
    if (data.success && data.customer) {
      const c = data.customer;
      const availCredit = c.pay_later_limit - c.pay_later_used;
      document.getElementById("customer-wallet-balance").innerText = formatVND(c.wallet_balance);
      document.getElementById("customer-pay-later-limit").innerText = formatVND(availCredit);
    }
  } catch (err) {
    console.error("Error loading customer:", err);
  }
}

async function prefetchTokens() {
  try {
    const res = await fetch("/api/v1/tokens/prefetch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: "USER_001" })
    });
    const data = await res.json();
    if (data.success && data.tokens.length > 0) {
      preloadedTokens = data.tokens;
      activeToken = preloadedTokens[0];
      document.getElementById("current-token-id").innerText = activeToken.token_id;
      logAuditEvent(`[CLIENT PREFETCH] Thiết bị đã tải trước ${data.tokens.length} token ngoại tuyến vào Secure Keystore.`);
    }
  } catch (err) {
    console.error("Error prefetching tokens:", err);
  }
}

function setupNetworkSwitch() {
  const toggle = document.getElementById("network-toggle");
  toggle.checked = isOnline;
  updateNetworkDisplay(isOnline);
}

function toggleNetworkMode(checked) {
  isOnline = checked;
  updateNetworkDisplay(isOnline);

  if (!isOnline) {
    logAuditEvent(`[NETWORK ALERT] Điện thoại mất sóng 4G/5G (Khu vực tầng hầm siêu thị). Chuyển sang cơ chế ngoại tuyến.`);
    showPosMessage("error", "⚠️ Khách hàng thông báo điện thoại mất sóng mạng 4G/Wi-Fi tại quầy!");
  } else {
    logAuditEvent(`[NETWORK] Đã khôi phục kết nối mạng 4G LTE trực tuyến.`);
  }
}

function updateNetworkDisplay(online) {
  const dot = document.getElementById("network-indicator-dot");
  const label = document.getElementById("network-text");
  const icons = document.getElementById("phone-signal-icons");

  if (online) {
    dot.innerText = "🟢";
    label.innerText = "4G LTE (Trực Tuyến)";
    label.style.color = "#10b981";
    icons.innerText = "📶 4G 🔋 98%";
  } else {
    dot.innerText = "🔴";
    label.innerText = "Mất Mạng / Tầng Hầm (Ngoại Tuyến)";
    label.style.color = "#f87171";
    icons.innerText = "✈️ No Signal 🔋 98%";
  }
}

function switchPhoneTab(tabId, btn) {
  document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".tab-btn").forEach(el => el.classList.remove("active"));

  document.getElementById(tabId).classList.add("active");
  btn.classList.add("active");
}

// 60-Second TOTP Cycle
function startTotpCycle() {
  generateClientQr();

  if (timerInterval) clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    countdownSeconds -= 1;
    if (countdownSeconds <= 0) {
      countdownSeconds = 60;
      generateClientQr();
    }
    document.getElementById("qr-timer-text").innerText = `${countdownSeconds}s`;
  }, 1000);
}

// Client-side TOTP computation & QR rendering
async function generateClientQr() {
  if (!activeToken) return;

  const now = Math.floor(Date.now() / 1000);
  const timeWindow = Math.floor(now / 60);

  try {
    // Generate TOTP code client-side using Web Cryptography API
    const totp = await computeBrowserTotp(activeToken.secret_key, timeWindow);
    const message = `V1:USER_001:${activeToken.token_id}:${now}:${totp}`;
    const signature = await computeBrowserHmac(activeToken.secret_key, message);

    const payloadObj = {
      ver: 1,
      uid: "USER_001",
      tid: activeToken.token_id,
      ts: now,
      totp: totp,
      sig: signature
    };

    const jsonStr = JSON.stringify(payloadObj);
    currentQrPayload = btoa(jsonStr).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

    // Render Canvas QR Code
    const container = document.getElementById("qrcode-canvas");
    container.innerHTML = "";
    qrCodeInstance = new QRCode(container, {
      text: currentQrPayload,
      width: 170,
      height: 170,
      colorDark: "#0f172a",
      colorLight: "#ffffff",
      correctLevel: QRCode.CorrectLevel.M
    });

  } catch (err) {
    console.error("Error generating client QR:", err);
  }
}

// Web Crypto HMAC-SHA256
async function computeBrowserHmac(secretKeyHex, messageStr) {
  const enc = new TextEncoder();
  const keyBytes = hexToUint8Array(secretKeyHex);
  const cryptoKey = await crypto.subtle.importKey(
    "raw",
    keyBytes,
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const signatureBytes = await crypto.subtle.sign("HMAC", cryptoKey, enc.encode(messageStr));
  return uint8ArrayToHex(new Uint8Array(signatureBytes));
}

// Dynamic truncation for TOTP
async function computeBrowserTotp(secretKeyHex, timeCounter) {
  const buffer = new ArrayBuffer(8);
  const view = new DataView(buffer);
  view.setBigUint64(0, BigInt(timeCounter), false);

  const keyBytes = hexToUint8Array(secretKeyHex);
  const cryptoKey = await crypto.subtle.importKey(
    "raw",
    keyBytes,
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const hashBytes = new Uint8Array(await crypto.subtle.sign("HMAC", cryptoKey, buffer));

  const offset = hashBytes[hashBytes.length - 1] & 0x0F;
  const codeInt = ((hashBytes[offset] & 0x7F) << 24 |
                   (hashBytes[offset + 1] & 0xFF) << 16 |
                   (hashBytes[offset + 2] & 0xFF) << 8 |
                   (hashBytes[offset + 3] & 0xFF));
  return String(codeInt % 1000000).padStart(6, "0");
}

function hexToUint8Array(hex) {
  const arr = new Uint8Array(hex.length / 2);
  for (let i = 0; i < arr.length; i++) {
    arr[i] = parseInt(hex.substr(i * 2, 2), 16);
  }
  return arr;
}

function uint8ArrayToHex(arr) {
  return Array.from(arr).map(b => b.toString(16).padStart(2, "0")).join("");
}

// Action: Simulate Cashier Scanning the Phone's Offline QR
async function simulateScanFromPhone() {
  if (!currentQrPayload) {
    alert("Mã QR chưa sẵn sàng.");
    return;
  }

  const { total } = calculateTotals();
  if (total <= 0) {
    showPosMessage("error", "Giỏ hàng quầy đang trống! Hãy chọn sản phẩm trước.");
    return;
  }

  try {
    const res = await fetch("/api/v1/payment/offline-qr", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        qr_data: currentQrPayload,
        amount: total
      })
    });
    const data = await res.json();

    if (data.success) {
      lastUsedPayload = currentQrPayload; // Save for replay attack test
      showPosMessage("success", `[THANH TOÁN THÀNH CÔNG] Mã GD: ${data.transaction_id} | Mã Auth: ${data.auth_code} | Số tiền: ${formatVND(data.amount_paid)} | Số dư ví còn lại: ${formatVND(data.remaining_balance)}`);
      logAuditEvent(`[OFFLINE QR SUCCESS] Quét thành công đơn ${formatVND(data.amount_paid)}. Nonce đã lưu chống Replay.`);
      clearCart();
      loadCustomerStatus();
      // Generate new QR immediately
      countdownSeconds = 60;
      generateClientQr();
    } else {
      showPosMessage("error", `[TỪ CHỐI GIAO DỊCH] ${data.message} (${data.error_code})`);
      logAuditEvent(`[OFFLINE QR REJECTED] ${data.error_code}: ${data.message}`);
    }
  } catch (err) {
    showPosMessage("error", "Lỗi kết nối máy quét: " + err.message);
  }
}

// Action: Deliberately test Anti-Replay Attack by scanning the old payload
async function simulateReplayAttack() {
  if (!lastUsedPayload) {
    alert("Bạn cần thực hiện 1 giao dịch thành công trước để có mã cũ đem thử lại gian lận!");
    return;
  }

  try {
    const res = await fetch("/api/v1/payment/offline-qr", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        qr_data: lastUsedPayload,
        amount: 50000
      })
    });
    const data = await res.json();

    if (!data.success) {
      showPosMessage("error", `[CHỐNG GIAN LẬN REPLAY THÀNH CÔNG] ${data.message}`);
      logAuditEvent(`[SECURITY PASS] Đã phát hiện và chặn đứng mã QR bị quét lại (Replay Attack blocked).`);
    } else {
      showPosMessage("error", "Cảnh báo: Mã lặp không bị chặn!");
    }
  } catch (err) {
    console.error(err);
  }
}

// Action: Simulate Apple Pay NFC Contactless Tap
async function simulateNFCTapFromPhone() {
  const { total } = calculateTotals();
  if (total <= 0) {
    showPosMessage("error", "Giỏ hàng quầy đang trống! Hãy chọn sản phẩm trước.");
    return;
  }

  // Animate NFC Terminal
  const nfcZone = document.getElementById("nfc-zone");
  nfcZone.style.background = "#bbf7d0";
  nfcZone.style.transform = "scale(1.03)";
  setTimeout(() => {
    nfcZone.style.background = "#f0fdf4";
    nfcZone.style.transform = "scale(1)";
  }, 600);

  try {
    const res = await fetch("/api/v1/payment/nfc-contactless", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        device_pan: "4111-XXXX-XXXX-1024",
        cryptogram: "ARQC_88B92C10E5",
        amount: total,
        user_id: "USER_001"
      })
    });
    const data = await res.json();

    if (data.success) {
      showPosMessage("success", `[NFC APPLE PAY THÀNH CÔNG] Mã GD: ${data.transaction_id} | Mã Phê Duyệt: ${data.auth_code} | Thẻ: ${data.card_type} | Số tiền: ${formatVND(data.amount_paid)}`);
      logAuditEvent(`[NFC CONTACTLESS] Apple Pay thành công không cần mạng di động qua chip Secure Element.`);
      clearCart();
      loadCustomerStatus();
    } else {
      showPosMessage("error", data.message);
    }
  } catch (err) {
    showPosMessage("error", "Lỗi NFC: " + err.message);
  }
}

// Action: Simulate In-Store Express Wi-Fi Connection
function simulateWiFiConnect() {
  alert("📶 ĐÃ KẾT NỐI THÀNH CÔNG VỚI '@SieuThi_ThanhToanNhanh'!\n\n• Cơ chế: Walled Garden (Bypass Captive Portal)\n• Không cần mật khẩu, không OTP SMS\n• Bạn có thể mở app Ngân hàng để chuyển khoản VietQR ngay bây giờ.");
  logAuditEvent(`[EXPRESS WI-FI] Thiết bị khách hàng đã vào mạng @SieuThi_ThanhToanNhanh (Bypass Captive Portal).`);
  // Switch network indicator
  updateNetworkDisplay(true);
}

// Action: Request In-Store Pay Later from Phone Tab
function requestInStorePayLater() {
  processPayLater();
}

// Reset Whole Demo Data
async function initDemoData() {
  if (!confirm("Khởi tạo lại toàn bộ dữ liệu demo về trạng thái ban đầu?")) return;
  try {
    const res = await fetch("/api/v1/init-demo", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      alert("Đã reset database thành công!");
      location.reload();
    }
  } catch (err) {
    alert("Lỗi reset: " + err.message);
  }
}

