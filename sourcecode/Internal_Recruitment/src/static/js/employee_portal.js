/**
 * employee_portal.js - Candidate & Internal Mobility Portal Controller
 * Handles employee authentication context, job catalog browsing,
 * real-time countdown calculation, 1-click apply, application tracking,
 * and notification alerts.
 */

let currentEmployeeId = "EMP-101";
let currentEmployeeData = null;
let allJobsList = [];
let selectedJobForApply = null;

// Initialize demo data across all 4 services
async function initDemoData() {
  if (!confirm("Bạn có chắc chắn muốn khởi tạo lại toàn bộ cơ sở dữ liệu mẫu cho cả 4 Microservices?")) {
    return;
  }
  try {
    const res = await fetch("/api/v1/init-demo", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      alert("✅ " + data.message);
      await loadEmployeeContext();
      await loadJobs();
      if (typeof loadKanbanApplications === "function") {
        await loadKanbanApplications();
      }
    } else {
      alert("❌ Lỗi: " + (data.message || data.error));
    }
  } catch (err) {
    alert("❌ Lỗi kết nối API Gateway: " + err.message);
  }
}

// Switch current active employee
async function switchEmployee(empId) {
  currentEmployeeId = empId;
  await loadEmployeeContext();
  await loadMyApplications();
  await loadNotifications();
}

// Load employee context and eligibility
async function loadEmployeeContext() {
  try {
    const res = await fetch(`/api/v1/employees/${currentEmployeeId}`);
    const data = await res.json();
    if (data.success && data.employee) {
      currentEmployeeData = data.employee;
      renderEmployeeHeader(data.employee);
    }
  } catch (err) {
    console.error("Lỗi tải thông tin nhân viên:", err);
  }
  await loadMyApplications();
  await loadNotifications();
}

// Render employee summary stats
function renderEmployeeHeader(emp) {
  const seniorityPill = document.getElementById("seniority-pill");
  const eligibilityPill = document.getElementById("eligibility-pill");

  if (seniorityPill) {
    seniorityPill.innerText = `⏳ Thâm niên: ${emp.months_at_company} tháng`;
  }

  if (eligibilityPill) {
    if (emp.months_at_company < 6) {
      eligibilityPill.innerText = `⚠️ Chưa đủ 6 tháng thâm niên`;
      eligibilityPill.style.color = "#f87171";
      eligibilityPill.style.borderColor = "#dc2626";
    } else if (emp.disciplinary_status !== "CLEAR") {
      eligibilityPill.innerText = `⚠️ Kỷ luật: ${emp.disciplinary_status}`;
      eligibilityPill.style.color = "#fbbf24";
      eligibilityPill.style.borderColor = "#d97706";
    } else {
      eligibilityPill.innerText = `✅ Đủ điều kiện chuyển đổi`;
      eligibilityPill.style.color = "#34d399";
      eligibilityPill.style.borderColor = "#059669";
    }
  }
}

// Portal tab switcher
function switchPortalTab(tab) {
  const jobsBtn = document.getElementById("tab-jobs-btn");
  const myappsBtn = document.getElementById("tab-myapps-btn");
  const jobsContent = document.getElementById("tab-jobs-content");
  const myappsContent = document.getElementById("tab-myapps-content");

  if (tab === "jobs") {
    jobsBtn.classList.add("active");
    myappsBtn.classList.remove("active");
    jobsContent.style.display = "flex";
    myappsContent.style.display = "none";
    loadJobs();
  } else {
    jobsBtn.classList.remove("active");
    myappsBtn.classList.add("active");
    jobsContent.style.display = "none";
    myappsContent.style.display = "flex";
    loadMyApplications();
  }
}

// Fetch and render jobs
async function loadJobs() {
  try {
    const res = await fetch("/api/v1/jobs");
    const data = await res.json();
    if (data.success) {
      allJobsList = data.jobs;
      filterJobs();
    }
  } catch (err) {
    console.error("Lỗi tải danh sách việc làm:", err);
  }
}

// Filter jobs by keyword, department, level, and active status
function filterJobs() {
  const keyword = (document.getElementById("job-search-input")?.value || "").toLowerCase().trim();
  const dept = document.getElementById("dept-filter")?.value || "";
  const level = document.getElementById("level-filter")?.value || "";
  const onlyActive = document.getElementById("only-active-checkbox")?.checked || false;

  const filtered = allJobsList.filter(job => {
    if (keyword) {
      const matchText = `${job.title} ${job.department} ${job.requirements} ${job.level}`.toLowerCase();
      if (!matchText.includes(keyword)) return false;
    }
    if (dept && job.department !== dept) return false;
    if (level && job.level !== level) return false;
    if (onlyActive && job.computed_status === "CLOSED") return false;
    return true;
  });

  renderJobsList(filtered);
}

// Render job cards with real-time status and countdown badges
function renderJobsList(jobs) {
  const container = document.getElementById("jobs-container");
  if (!container) return;

  if (jobs.length === 0) {
    container.innerHTML = `<div class="loading-placeholder">Không tìm thấy vị trí tuyển dụng phù hợp với bộ lọc.</div>`;
    return;
  }

  container.innerHTML = jobs.map(job => {
    let statusBadge = "";
    const hours = job.remaining_hours || 0;

    if (job.computed_status === "CLOSED" || hours <= 0) {
      statusBadge = `<span class="badge-closed">🔴 Đã hết hạn</span>`;
    } else if (job.computed_status === "CLOSING_SOON" || hours <= 72) {
      const remainingDays = Math.max(1, Math.ceil(hours / 24));
      statusBadge = `<span class="badge-closing-soon">⏳ Sắp hết hạn (còn ${hours} giờ ~ ${remainingDays} ngày)</span>`;
    } else {
      const days = Math.floor(hours / 24);
      statusBadge = `<span class="badge-open">🟢 Đang mở (còn ${days} ngày)</span>`;
    }

    const isClosed = (job.computed_status === "CLOSED" || hours <= 0);

    return `
      <div class="job-card">
        <div class="job-card-header">
          <div>
            <div class="job-title">${escapeHtml(job.title)}</div>
            <div class="job-meta-row" style="margin-top: 4px;">
              <span class="job-meta-tag">🏢 ${escapeHtml(job.department)}</span>
              <span class="job-meta-tag">🎖️ ${escapeHtml(job.level)}</span>
              <span class="job-meta-tag">👥 Tuyển: ${job.headcount} người</span>
              <span class="job-salary">💰 ${escapeHtml(job.salary_range)} VNĐ</span>
            </div>
          </div>
          <div>${statusBadge}</div>
        </div>

        <div class="job-desc">
          <strong>Yêu cầu:</strong> ${escapeHtml(job.requirements || "Xem chi tiết JD...")}
        </div>

        <div class="job-privacy-pill">
          🔒 <strong>Bảo mật:</strong> Đơn nộp được mã hóa. Quản lý phòng ban cũ hoàn toàn không hay biết.
        </div>

        <div class="job-card-actions">
          <button class="btn-apply" 
                  ${isClosed ? "disabled" : ""} 
                  onclick="openApplyModal('${job.job_id}')">
            ${isClosed ? "Đã Hết Hạn" : "🚀 Ứng Tuyển Nhanh"}
          </button>
        </div>
      </div>
    `;
  }).join("");
}

// Open 1-Click Apply Modal
function openApplyModal(jobId) {
  const job = allJobsList.find(j => j.job_id === jobId);
  if (!job) return;

  selectedJobForApply = job;

  const summary = document.getElementById("apply-job-summary");
  if (summary) {
    summary.innerHTML = `
      <strong style="color: #38bdf8; font-size: 0.95rem;">${escapeHtml(job.title)}</strong><br>
      <span style="color: #94a3b8;">Phòng ban: ${escapeHtml(job.department)} | Cấp bậc: ${escapeHtml(job.level)} | Hạn chót: ${escapeHtml(job.deadline_date)}</span>
    `;
  }

  const nameInput = document.getElementById("apply-emp-name");
  const deptInput = document.getElementById("apply-emp-dept");

  if (currentEmployeeData) {
    if (nameInput) nameInput.value = `${currentEmployeeData.name} (${currentEmployeeData.employee_id})`;
    if (deptInput) deptInput.value = `${currentEmployeeData.current_department} - Thâm niên: ${currentEmployeeData.months_at_company} tháng`;
  }

  const clInput = document.getElementById("apply-cover-letter");
  if (clInput) {
    clInput.value = "Tôi mong muốn ứng tuyển vị trí này để phát huy năng lực và đóng góp lâu dài cho công ty.";
    document.getElementById("cover-char-count").innerText = `${clInput.value.length} ký tự`;
  }

  const modal = document.getElementById("apply-modal");
  if (modal) modal.style.display = "flex";
}

function closeApplyModal() {
  const modal = document.getElementById("apply-modal");
  if (modal) modal.style.display = "none";
  selectedJobForApply = null;
}

// Submit Application
async function submitApplication() {
  if (!selectedJobForApply) return;

  const clInput = document.getElementById("apply-cover-letter");
  const coverLetter = (clInput?.value || "").trim();
  const resumeSelect = document.getElementById("apply-resume-select");
  const resumeFile = resumeSelect?.value || "HoSo_NoiBo.pdf";

  if (coverLetter.length < 10) {
    alert("❌ Thư nguyện vọng (Cover Letter) phải có độ dài tối thiểu 10 ký tự (Kiểm thử biên BVA)!");
    return;
  }

  try {
    const res = await fetch("/api/v1/applications/apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        job_id: selectedJobForApply.job_id,
        employee_id: currentEmployeeId,
        cover_letter: coverLetter,
        resume_file: resumeFile
      })
    });

    const data = await res.json();
    if (data.success) {
      alert(`🎉 Chúc mừng! ${data.message}\nMã hồ sơ: ${data.application_id}`);
      closeApplyModal();
      await loadEmployeeContext();
      await loadMyApplications();
      await loadNotifications();
      if (typeof loadKanbanApplications === "function") {
        await loadKanbanApplications();
      }
      // Auto switch to My Applications tab
      switchPortalTab("myapps");
    } else {
      alert(`❌ Ứng tuyển không thành công:\n[${data.error_code || "LỖI"}]: ${data.message}`);
    }
  } catch (err) {
    alert("❌ Lỗi gửi đơn ứng tuyển: " + err.message);
  }
}

// Load candidate's personal applications
async function loadMyApplications() {
  try {
    const res = await fetch(`/api/v1/applications/my-applications?employee_id=${currentEmployeeId}`);
    const data = await res.json();
    if (data.success) {
      const countSpan = document.getElementById("my-apps-count");
      const activePill = document.getElementById("active-apps-pill");

      if (countSpan) countSpan.innerText = data.applications.length;
      if (activePill) activePill.innerText = `📋 Đang ứng tuyển: ${data.active_count}/3`;

      renderMyApplicationsList(data.applications);
    }
  } catch (err) {
    console.error("Lỗi tải hồ sơ của tôi:", err);
  }
}

// Render candidate's application pipeline stepper
function renderMyApplicationsList(apps) {
  const container = document.getElementById("myapps-container");
  if (!container) return;

  if (apps.length === 0) {
    container.innerHTML = `<div class="loading-placeholder">Bạn chưa nộp hồ sơ cho vị trí nào. Hãy duyệt bảng tin và ứng tuyển nhé!</div>`;
    return;
  }

  const steps = [
    { key: "APPLIED", label: "Đã nộp" },
    { key: "HR_SCREENING", label: "Sàng lọc" },
    { key: "INTERVIEW", label: "Phỏng vấn" },
    { key: "OFFER", label: "Đề nghị (Offer)" },
    { key: "TRANSFERRED", label: "Điều chuyển" }
  ];

  container.innerHTML = apps.map(app => {
    const currentStatus = app.status;
    const isRejected = (currentStatus === "REJECTED");
    const currentStepIdx = steps.findIndex(s => s.key === currentStatus);

    const stepperHtml = steps.map((step, idx) => {
      let nodeClass = "step-node";
      if (!isRejected) {
        if (idx < currentStepIdx) nodeClass += " completed";
        else if (idx === currentStepIdx) nodeClass += " active";
      } else {
        if (idx === currentStepIdx || (currentStepIdx === -1 && idx === 0)) nodeClass += " rejected";
      }

      return `
        <div class="${nodeClass}">
          <div class="step-circle">${idx + 1}</div>
          <span>${step.label}</span>
        </div>
      `;
    }).join("");

    return `
      <div class="myapp-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
          <div>
            <strong style="color: #38bdf8; font-size: 0.95rem;">${escapeHtml(app.job_title)}</strong>
            <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 2px;">
              Mã hồ sơ: <strong>${app.application_id}</strong> | Ngày nộp: ${app.applied_at}
            </div>
          </div>
          <div>
            <span class="job-meta-tag" style="color: ${isRejected ? '#f87171' : '#34d399'}; font-weight: bold;">
              ${isRejected ? "❌ TỪ CHỐI" : currentStatus}
            </span>
          </div>
        </div>

        <!-- Stepper Component -->
        <div class="stepper">
          ${stepperHtml}
        </div>

        <div style="background: #0f172a; padding: 8px 12px; border-radius: 6px; font-size: 0.78rem; border: 1px solid #334155;">
          <div><strong>📌 Thư nguyện vọng:</strong> "${escapeHtml(app.cover_letter)}"</div>
          ${app.interview_score !== null ? `<div style="margin-top: 4px; color: #34d399;"><strong>🎯 Điểm phỏng vấn:</strong> ${app.interview_score}/100</div>` : ""}
          <div style="margin-top: 4px; color: #fbbf24;"><strong>💬 Ghi chú từ HR:</strong> ${escapeHtml(app.hr_notes || "Hồ sơ đang trong chu trình xem xét")}</div>
        </div>
      </div>
    `;
  }).join("");
}

// Notifications drawer toggling
async function toggleNotificationDrawer() {
  const drawer = document.getElementById("notification-drawer");
  if (!drawer) return;

  if (drawer.style.display === "none") {
    drawer.style.display = "flex";
    await loadNotifications();
  } else {
    drawer.style.display = "none";
  }
}

// Load notifications
async function loadNotifications() {
  try {
    const res = await fetch(`/api/v1/notifications?employee_id=${currentEmployeeId}`);
    const data = await res.json();
    if (data.success) {
      const badge = document.getElementById("noti-badge");
      if (badge) badge.innerText = data.unread_count || 0;
      renderNotificationsList(data.notifications);
    }
  } catch (err) {
    console.error("Lỗi tải thông báo:", err);
  }
}

// Render notifications
function renderNotificationsList(notis) {
  const container = document.getElementById("noti-list");
  if (!container) return;

  if (notis.length === 0) {
    container.innerHTML = `<div class="loading-placeholder" style="padding: 15px;">Không có thông báo mới.</div>`;
    return;
  }

  container.innerHTML = notis.map(n => `
    <div class="noti-item ${n.is_read ? '' : 'unread'}">
      <div class="noti-item-title">${escapeHtml(n.title)}</div>
      <div class="noti-item-msg">${escapeHtml(n.message)}</div>
      <div class="noti-item-time">🕒 ${n.created_at}</div>
    </div>
  `).join("");
}

// Utility: HTML escape
function escapeHtml(text) {
  if (!text) return "";
  return text.toString()
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

