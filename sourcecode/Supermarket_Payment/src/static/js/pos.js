/**
 * pos.js - Cashier Point-of-Sale (POS) Operations Logic
 * Handles cart scanning, hotkeys [F7], [F8], [F9], [F10], parked order suspension and resumption.
 */

let currentCart = [];
let availableProducts = [];
let lastParkedId = null;

document.addEventListener("DOMContentLoaded", () => {
  loadProducts();
  refreshParkedOrders();
  setupKeyboardShortcuts();
});

// Load products from backend
async function loadProducts() {
  try {
    const res = await fetch("/api/v1/products");
    const data = await res.json();
    if (data.success) {
      availableProducts = data.products;
      renderProductsGrid(availableProducts);
      // Add default 2 items for immediate demonstration
      if (availableProducts.length >= 2 && currentCart.length === 0) {
        addToCart(availableProducts[0]); // Vinamilk 1L
        addToCart(availableProducts[1]); // Thịt bò Úc
      }
    }
  } catch (err) {
    console.error("Error loading products:", err);
  }
}

function renderProductsGrid(products) {
  const container = document.getElementById("products-list");
  container.innerHTML = "";
  products.forEach(p => {
    const item = document.createElement("div");
    item.className = "product-item";
    item.innerHTML = `
      <div class="p-name">${p.name}</div>
      <div class="p-price">${formatVND(p.price)}</div>
      <div style="font-size: 0.68rem; color: #64748b; margin-top: 2px;">Mã: ${p.barcode}</div>
    `;
    item.onclick = () => addToCart(p);
    container.appendChild(item);
  });
}

function addToCart(product) {
  const existing = currentCart.find(i => i.product_id === product.product_id);
  if (existing) {
    existing.quantity += 1;
  } else {
    currentCart.push({
      product_id: product.product_id,
      name: product.name,
      price: product.price,
      quantity: 1
    });
  }
  renderCart();
}

function updateQuantity(index, delta) {
  if (!currentCart[index]) return;
  currentCart[index].quantity += delta;
  if (currentCart[index].quantity <= 0) {
    currentCart.splice(index, 1);
  }
  renderCart();
}

function clearCart() {
  currentCart = [];
  renderCart();
  hidePosMessage();
}

function calculateTotals() {
  const subtotal = currentCart.reduce((acc, item) => acc + item.price * item.quantity, 0);
  const vat = Math.round(subtotal * 0.08);
  const total = subtotal + vat;
  return { subtotal, vat, total };
}

function renderCart() {
  const tbody = document.getElementById("cart-items-body");
  const countSpan = document.getElementById("cart-item-count");
  
  if (currentCart.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #94a3b8; padding: 20px;">Giỏ hàng đang trống. Hãy click chọn sản phẩm!</td></tr>`;
    countSpan.innerText = "0 món";
    document.getElementById("subtotal-amount").innerText = "0 đ";
    document.getElementById("vat-amount").innerText = "0 đ";
    document.getElementById("total-amount").innerText = "0 đ";
    return;
  }

  const { subtotal, vat, total } = calculateTotals();
  const totalItems = currentCart.reduce((sum, i) => sum + i.quantity, 0);
  countSpan.innerText = `${totalItems} món`;

  tbody.innerHTML = currentCart.map((item, idx) => `
    <tr>
      <td><strong>${item.name}</strong></td>
      <td>${formatVND(item.price)}</td>
      <td style="text-align: center;">
        <button class="btn-qty" onclick="updateQuantity(${idx}, -1)">-</button>
        <span style="font-weight: bold; margin: 0 6px;">${item.quantity}</span>
        <button class="btn-qty" onclick="updateQuantity(${idx}, 1)">+</button>
      </td>
      <td style="text-align: right; font-weight: 600;">${formatVND(item.price * item.quantity)}</td>
      <td style="text-align: center;"><button style="background: none; border: none; cursor: pointer; color: #ef4444;" onclick="updateQuantity(${idx}, -999)">×</button></td>
    </tr>
  `).join("");

  document.getElementById("subtotal-amount").innerText = formatVND(subtotal);
  document.getElementById("vat-amount").innerText = formatVND(vat);
  document.getElementById("total-amount").innerText = formatVND(total);
}

// [F8] Suspend / Park Cart
async function parkCurrentCart() {
  if (currentCart.length === 0) {
    showPosMessage("error", "Giỏ hàng đang trống, không thể treo đơn!");
    return;
  }

  const { total } = calculateTotals();

  try {
    const res = await fetch("/api/v1/pos/park-order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        store_id: "SUPERMARKET_01",
        terminal_id: "LINE_01",
        cashier_id: "LINH_1024",
        customer_id: "USER_001",
        total_amount: total,
        order_items: currentCart
      })
    });
    const data = await res.json();
    if (data.success) {
      lastParkedId = data.park_id;
      showPosMessage("success", `[F8 THÀNH CÔNG] Đã in 'Phiếu Giữ Giỏ Hàng' mã: ${data.park_id}. Quầy đã sẵn sàng phục vụ khách tiếp theo!`);
      logAuditEvent(`[POS PARK] Đơn hàng được treo với mã ${data.park_id}, tổng tiền: ${formatVND(data.total_amount)}`);
      currentCart = [];
      renderCart();
      refreshParkedOrders();
    } else {
      showPosMessage("error", data.message || "Lỗi khi treo đơn");
    }
  } catch (err) {
    showPosMessage("error", "Không thể kết nối đến máy chủ POS: " + err.message);
  }
}

// [F9] Prompt & Resume Parked Cart
async function promptResumeOrder(prefilledId = null) {
  const parkId = prefilledId || prompt("Nhập mã vạch trên phiếu giữ giỏ hàng (ví dụ: " + (lastParkedId || "HOLD-YYYYMMDD-XXXX") + "):");
  if (!parkId) return;

  try {
    const res = await fetch("/api/v1/pos/resume-order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ park_id: parkId })
    });
    const data = await res.json();
    if (data.success) {
      currentCart = data.order.items;
      renderCart();
      showPosMessage("success", `[F9 THÀNH CÔNG] Đã khôi phục hoàn chỉnh giỏ hàng ${parkId} (${data.order.items.length} món sản phẩm).`);
      logAuditEvent(`[POS RESUME] Đã khôi phục đơn treo ${parkId}, tiếp tục thanh toán`);
      refreshParkedOrders();
    } else {
      showPosMessage("error", data.message || "Không thể khôi phục đơn treo!");
    }
  } catch (err) {
    showPosMessage("error", "Lỗi: " + err.message);
  }
}

// Refresh Suspended Orders Queue
async function refreshParkedOrders() {
  try {
    const res = await fetch("/api/v1/pos/parked-orders");
    const data = await res.json();
    const countText = document.getElementById("parked-count-text");
    const quickActions = document.getElementById("parked-quick-actions");

    if (data.success && data.parked_orders.length > 0) {
      countText.innerHTML = `<strong>${data.parked_orders.length} đơn đang chờ</strong>`;
      quickActions.innerHTML = data.parked_orders.map(o => `
        <button class="hotkey-btn btn-resume" style="padding: 2px 8px; font-size: 0.72rem;" onclick="promptResumeOrder('${o.park_id}')">
          Phục hồi: ${o.park_id} (${formatVND(o.total_amount)})
        </button>
      `).join(" ");
    } else {
      countText.innerText = "Chưa có đơn treo nào";
      quickActions.innerHTML = "";
    }
  } catch (err) {
    console.error(err);
  }
}

// [F10] Process Member Pay-Later (In-store Trust Micro-Credit)
async function processPayLater() {
  const currentTotal = calculateTotals().total;
  const cartQty = currentCart.reduce((acc, i) => acc + i.quantity, 0);

  // Mở hộp thoại nhập số tiền vay để kiểm thử biên y3
  const defaultAmount = currentTotal > 0 ? currentTotal : 0;
  const loanPrompt = prompt(
    "💳 [F10 TẠM ỨNG PAY-LATER]\n\n" +
    "Nhập số tiền muốn tạm ứng nợ (VNĐ):\n" +
    "(Hạn mức biên hợp lệ: 1.000đ - 500.000đ | Nhập 0 để test ca vi phạm biên y3):",
    defaultAmount
  );
  if (loanPrompt === null) return; // Người dùng bấm Hủy

  const loanAmount = parseInt(loanPrompt.replace(/\D/g, "") || "0");

  // Mở hộp thoại nhập điểm tín nhiệm để kiểm thử biên y4
  const scorePrompt = prompt(
    "📊 [F10 KIỂM TRA ĐIỂM TÍN NHIỆM]\n\n" +
    "Nhập điểm tín nhiệm hội viên (FICO Score):\n" +
    "(Ngưỡng sàn bảo lãnh: >= 650 điểm | Thang đo: 650 - 850 | Nhập 649 để test ca vi phạm biên y4):",
    "649"
  );
  if (scorePrompt === null) return; // Người dùng bấm Hủy

  const creditScore = parseInt(scorePrompt.replace(/\D/g, "") || "0");

  // Gửi thẩm định toàn diện 4 biến tới Gateway
  try {
    const res = await fetch("/api/checkout/validate-all", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        amount: currentTotal,
        cart_quantity: cartQty,
        loan_amount: loanAmount,
        credit_score: creditScore
      })
    });
    const result = await res.json();

    if (result.status === "APPROVED_ALL") {
      alert(
        "✅ [F10 THÀNH CÔNG - HTTP 200 OK]\n\n" +
        `• Khoản vay (y3): ${formatVND(loanAmount)}\n` +
        `• Điểm tín nhiệm (y4): ${creditScore} (ĐỦ ĐIỀU KIỆN >= 650)\n` +
        `• Số lượng món (y2): ${cartQty} món\n` +
        `• Tổng tiền đơn (y1): ${formatVND(currentTotal)}\n\n` +
        `Trạng thái: ${result.message}\n` +
        "Hóa đơn nợ đã được tạo thành công!"
      );
      showPosMessage("success", `[F10 THÀNH CÔNG] Đã cấp tạm ứng ${formatVND(loanAmount)} cho hội viên (Điểm: ${creditScore}).`);
      logAuditEvent(`[PAY LATER APPROVED] Tạm ứng ${formatVND(loanAmount)} thành công.`);
      currentCart = [];
      renderCart();
      if (window.loadCustomerStatus) window.loadCustomerStatus();
    } else {
      const errName = result.error || "REJECTED";
      const violations = (result.violations || []).join(", ");
      const details = (result.details || []).map(d => `• ${d}`).join("\n");

      alert(
        "❌ [TỪ CHỐI TẠM ỨNG PAY-LATER - HTTP 400 BAD REQUEST]\n\n" +
        `Hệ thống chặn giao dịch do vi phạm giá trị biên:\n` +
        `• Lỗi chặn đầu tiên: ${errName}\n` +
        `• Danh sách vi phạm biên: ${violations}\n\n` +
        `Chi tiết kiểm tra:\n${details}`
      );
      showPosMessage("error", `[TỪ CHỐI F10] ${errName}: ${(result.details || [])[0] || 'Vi phạm biên'}`);
      logAuditEvent(`[PAY LATER REJECTED] Từ chối tạm ứng: ${errName}`);
    }
  } catch (err) {
    alert("Lỗi kết nối kiểm tra: " + err.message);
  }
}

// [F7] Trigger Scan Customer QR from POS side
function triggerScanCustomerQR() {
  if (window.simulateScanFromPhone) {
    window.simulateScanFromPhone();
  } else {
    showPosMessage("error", "Không nhận diện được máy khách.");
  }
}

// Keyboard Hotkey Listener
function setupKeyboardShortcuts() {
  window.addEventListener("keydown", (e) => {
    if (e.key === "F7") {
      e.preventDefault();
      triggerScanCustomerQR();
    } else if (e.key === "F8") {
      e.preventDefault();
      parkCurrentCart();
    } else if (e.key === "F9") {
      e.preventDefault();
      promptResumeOrder();
    } else if (e.key === "F10") {
      e.preventDefault();
      processPayLater();
    }
  });
}

function showPosMessage(type, msg) {
  const el = document.getElementById("pos-message");
  el.className = `pos-message-banner ${type}`;
  el.innerText = msg;
  el.style.display = "block";
}

function hidePosMessage() {
  const el = document.getElementById("pos-message");
  el.style.display = "none";
}

function formatVND(amount) {
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(amount).replace("₫", "đ");
}

function logAuditEvent(text) {
  const container = document.getElementById("audit-logs");
  const countEl = document.getElementById("log-count");
  const now = new Date().toLocaleTimeString();
  const div = document.createElement("div");
  div.className = "audit-entry";
  div.innerHTML = `<span>[${now}] ${text}</span>`;
  container.prepend(div);

  const totalLogs = container.children.length;
  countEl.innerText = `${totalLogs} sự kiện`;
}


