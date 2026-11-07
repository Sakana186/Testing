/**
 * hr_dashboard.js - HR Recruitment Command Center & Kanban Pipeline Controller
 * Coordinates candidate progression across hiring stages, job postings,
 * deadline extensions, interview scoring, and inter-service updates.
 */

let allKanbanApps = [];
let activeAppForAction = null;

// Load all applications into Kanban board
async function loadKanbanApplications() {
  try {
    const res = await fetch("/api/v1/applications");
    const data = await res.json();
    if (data.success) {
      allKanbanApps = data.applications;
      renderKanbanBoard(data.applications);
    }
  } catch (err) {
    console.error("Lỗi tải danh sách Kanban:", err);
  }
}

// Render 5 Kanban Columns
function renderKanbanBoard(apps) {
  const colApplied = document.getElementById("cards-applied");
  const colScreening = document.getElementById("cards-screening");
  const colInterview = document.getElementById("cards-interview");
  const colOffer = document.getElementById("cards-offer");
  const colResult = document.getElementById("cards-result");

  const countApplied = document.getElementById("count-applied");
  const countScreening = document.getElementById("count-screening");
  const countInterview = document.getElementById("count-interview");
  const countOffer = document.getElementById("count-offer");
  const countResult = document.getElementById("count-result");

  if (!colApplied) return;

  // Clear columns
  colApplied.innerHTML = "";
  colScreening.innerHTML = "";
  colInterview.innerHTML = "";
  colOffer.innerHTML = "";
  colResult.innerHTML = "";

  let cApplied = 0, cScreening = 0, cInterview = 0, cOffer = 0, cResult = 0;

  apps.forEach(app => {
    const cardHtml = createKanbanCardHtml(app);
    switch (app.status) {
      case "APPLIED":
        colApplied.innerHTML += cardHtml;
        cApplied++;
        break;
      case "HR_SCREENING":
        colScreening.innerHTML += cardHtml;
        cScreening++;
        break;
      case "INTERVIEW":
        colInterview.innerHTML += cardHtml;
        cInterview++;
        break;
      case "OFFER":
        colOffer.innerHTML += cardHtml;
        cOffer++;
        break;
      case "TRANSFERRED":
      case "REJECTED":
      case "WITHDRAWN":
        colResult.innerHTML += cardHtml;
        cResult++;
        break;
      default:
        colApplied.innerHTML += cardHtml;
        cApplied++;
    }
  });

  if (countApplied) countApplied.innerText = cApplied;
  if (countScreening) countScreening.innerText = cScreening;
  if (countInterview) countInterview.innerText = cInterview;
  if (countOffer) countOffer.innerText = cOffer;
  if (countResult) countResult.innerText = cResult;
}

// Create individual Kanban Card HTML
function createKanbanCardHtml(app) {
  const isRejected = (app.status === "REJECTED");
  const isTransferred = (app.status === "TRANSFERRED");

  let actionBtns = "";

  if (app.status === "APPLIED") {
    actionBtns = `
      <button class="btn-card-action" onclick="quickUpdateStatus('${app.application_id}', 'HR_SCREENING')">Sàng Lọc ➔</button>
      <button class="btn-card-action" style="color: #f87171;" onclick="quickUpdateStatus('${app.application_id}', 'REJECTED')">✕ Loại</button>
    `;
  } else if (app.status === "HR_SCREENING") {
    actionBtns = `
      <button class="btn-card-action" onclick="quickUpdateStatus('${app.application_id}', 'INTERVIEW')">Phỏng Vấn ➔</button>
      <button class="btn-card-action" style="color: #f87171;" onclick="quickUpdateStatus('${app.application_id}', 'REJECTED')">✕ Loại</button>
    `;
  } else if (app.status === "INTERVIEW") {
    actionBtns = `
      <button class="btn-card-action" style="color: #a78bfa;" onclick="openKanbanActionModal('${app.application_id}', 'OFFER')">📝 Đánh Giá / Offer</button>
      <button class="btn-card-action" style="color: #f87171;" onclick="quickUpdateStatus('${app.application_id}', 'REJECTED')">✕ Loại</button>
    `;
  } else if (app.status === "OFFER") {
    actionBtns = `
      <button class="btn-card-action" style="color: #34d399;" onclick="quickUpdateStatus('${app.application_id}', 'TRANSFERRED')">✅ Hoàn Tất Chuyển</button>
      <button class="btn-card-action" style="color: #f87171;" onclick="quickUpdateStatus('${app.application_id}', 'REJECTED')">✕ Hủy Offer</button>
    `;
  } else {
    actionBtns = `<span style="font-size: 0.68rem; color: #64748b;">Đã kết thúc chu trình</span>`;
  }

  return `
    <div class="kanban-card">
      <div class="card-candidate-name">
        <span>👤 ${escapeHtml(app.employee_name)}</span>
        <span style="font-size: 0.68rem; color: #94a3b8;">${app.application_id}</span>
      </div>
      <div class="card-dept">Phòng ban: ${escapeHtml(app.department)}</div>
      <div class="card-target-job">🎯 ${escapeHtml(app.job_title)}</div>
      
      ${app.interview_score !== null ? `
        <div class="card-score">Điểm PV: ${app.interview_score}/100</div>
      ` : ""}

      ${app.hr_notes ? `
        <div style="font-size: 0.7rem; color: #cbd5e1; font-style: italic; background: #0b0f19; padding: 4px; border-radius: 4px;">
          "${escapeHtml(app.hr_notes)}"
        </div>
      ` : ""}

      <div class="card-date">Nộp: ${app.applied_at}</div>

      <div class="card-actions">
        ${actionBtns}
      </div>
    </div>
  `;
}

// Quick 1-click status progression
async function quickUpdateStatus(appId, newStatus) {
  const note = prompt(`Nhập ghi chú nhân sự (HR Note) khi chuyển sang [${newStatus}]:`, "Đạt tiêu chí vòng tuyển chọn");
  if (note === null) return; // cancelled

  try {
    const res = await fetch("/api/v1/applications/update-status", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        application_id: appId,
        new_status: newStatus,
        hr_notes: note
      })
    });
    const data = await res.json();
    if (data.success) {
      await loadKanbanApplications();
      if (typeof loadMyApplications === "function") await loadMyApplications();
      if (typeof loadNotifications === "function") await loadNotifications();
    } else {
      alert("❌ Lỗi cập nhật: " + data.message);
    }
  } catch (err) {
    alert("❌ Lỗi mạng: " + err.message);
  }
}

// Open Action Modal (Scoring & Notes)
function openKanbanActionModal(appId, targetStatus = "OFFER") {
  const app = allKanbanApps.find(a => a.application_id === appId);
  if (!app) return;

  activeAppForAction = app;
  document.getElementById("action-app-id").value = appId;
  document.getElementById("action-new-status").value = targetStatus;
  document.getElementById("action-score").value = "85";
  document.getElementById("action-hr-notes").value = "Kỹ năng chuyên môn tốt, phỏng vấn xuất sắc, đáp ứng chuẩn vị trí mới.";

  const modal = document.getElementById("kanban-action-modal");
  if (modal) modal.style.display = "flex";
}

function closeKanbanActionModal() {
  const modal = document.getElementById("kanban-action-modal");
  if (modal) modal.style.display = "none";
  activeAppForAction = null;
}

// Submit Kanban Transition
async function submitKanbanTransition() {
  const appId = document.getElementById("action-app-id").value;
  const newStatus = document.getElementById("action-new-status").value;
  const scoreVal = document.getElementById("action-score").value;
  const notes = document.getElementById("action-hr-notes").value;

  const score = scoreVal ? parseInt(scoreVal, 10) : null;

  try {
    const res = await fetch("/api/v1/applications/update-status", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        application_id: appId,
        new_status: newStatus,
        interview_score: score,
        hr_notes: notes
      })
    });
    const data = await res.json();
    if (data.success) {
      alert(`✅ Đã cập nhật hồ sơ ${appId} sang trạng thái [${newStatus}]!`);
      closeKanbanActionModal();
      await loadKanbanApplications();
      if (typeof loadMyApplications === "function") await loadMyApplications();
      if (typeof loadNotifications === "function") await loadNotifications();
    } else {
      alert("❌ Lỗi: " + data.message);
    }
  } catch (err) {
    alert("❌ Lỗi mạng: " + err.message);
  }
}

// MODAL 2: Create New Job
function openNewJobModal() {
  // Set default deadline 14 days from now
  const d = new Date();
  d.setDate(d.getDate() + 14);
  const defaultDeadline = d.toISOString().split("T")[0];
  const deadlineInput = document.getElementById("new-job-deadline");
  if (deadlineInput) deadlineInput.value = defaultDeadline;

  const modal = document.getElementById("new-job-modal");
  if (modal) modal.style.display = "flex";
}

function closeNewJobModal() {
  const modal = document.getElementById("new-job-modal");
  if (modal) modal.style.display = "none";
}

async function submitCreateJob() {
  const title = document.getElementById("new-job-title")?.value.trim();
  const dept = document.getElementById("new-job-dept")?.value;
  const level = document.getElementById("new-job-level")?.value;
  const headcount = parseInt(document.getElementById("new-job-headcount")?.value || "1", 10);
  const salary = document.getElementById("new-job-salary")?.value.trim();
  const deadline = document.getElementById("new-job-deadline")?.value;
  const reqs = document.getElementById("new-job-requirements")?.value.trim();

  if (!title || !deadline) {
    alert("❌ Tiêu đề và Hạn chót không được để trống!");
    return;
  }

  try {
    const res = await fetch("/api/v1/jobs/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: title,
        department: dept,
        level: level,
        headcount: headcount,
        salary_range: salary,
        deadline_date: deadline,
        requirements: reqs
      })
    });
    const data = await res.json();
    if (data.success) {
      alert(`🎉 Đã đăng tuyển vị trí mới thành công: [${data.job.job_id}] ${data.job.title}`);
      closeNewJobModal();
      if (typeof loadJobs === "function") await loadJobs();
    } else {
      alert("❌ Lỗi tạo tin tuyển: " + data.message);
    }
  } catch (err) {
    alert("❌ Lỗi kết nối: " + err.message);
  }
}

// MODAL 3: Manage Deadlines
async function openManageDeadlinesModal() {
  try {
    const res = await fetch("/api/v1/jobs");
    const data = await res.json();
    if (data.success) {
      renderDeadlinesTable(data.jobs);
      const modal = document.getElementById("deadlines-modal");
      if (modal) modal.style.display = "flex";
    }
  } catch (err) {
    alert("Lỗi tải danh sách tin tuyển dụng: " + err.message);
  }
}

function closeManageDeadlinesModal() {
  const modal = document.getElementById("deadlines-modal");
  if (modal) modal.style.display = "none";
}

function renderDeadlinesTable(jobs) {
  const tbody = document.getElementById("deadline-jobs-table-body");
  if (!tbody) return;

  tbody.innerHTML = jobs.map(job => {
    return `
      <tr>
        <td><strong>${job.job_id}</strong></td>
        <td>${escapeHtml(job.title)}</td>
        <td><span style="color: #38bdf8;">${job.deadline_date}</span></td>
        <td>
          <span style="font-weight: bold; color: ${job.computed_status === 'CLOSED' ? '#f87171' : '#34d399'};">
            ${job.computed_status}
          </span>
        </td>
        <td>
          <button class="btn-card-action" onclick="extendDeadlinePrompt('${job.job_id}')">➕ Gia Hạn 7 Ngày</button>
          ${job.computed_status !== 'CLOSED' ? `
            <button class="btn-card-action" style="color: #f87171;" onclick="closeJobPrompt('${job.job_id}')">🔒 Đóng Tin Ngay</button>
          ` : ""}
        </td>
      </tr>
    `;
  }).join("");
}

async function extendDeadlinePrompt(jobId) {
  const d = new Date();
  d.setDate(d.getDate() + 7);
  const newDate = d.toISOString().split("T")[0];

  const targetDate = prompt(`Nhập ngày hạn chót mới (YYYY-MM-DD):`, newDate);
  if (!targetDate) return;

  try {
    const res = await fetch("/api/v1/jobs/extend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: jobId, new_deadline: targetDate })
    });
    const data = await res.json();
    if (data.success) {
      alert("✅ " + data.message);
      await openManageDeadlinesModal();
      if (typeof loadJobs === "function") await loadJobs();
    } else {
      alert("❌ Lỗi: " + data.message);
    }
  } catch (err) {
    alert("❌ Lỗi mạng: " + err.message);
  }
}

async function closeJobPrompt(jobId) {
  if (!confirm(`Bạn có chắc chắn muốn ĐÓNG tin tuyển dụng ${jobId} ngay bây giờ? Sau khi đóng, ứng viên không thể nộp đơn nữa.`)) {
    return;
  }

  try {
    const res = await fetch("/api/v1/jobs/close", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: jobId })
    });
    const data = await res.json();
    if (data.success) {
      alert("✅ " + data.message);
      await openManageDeadlinesModal();
      if (typeof loadJobs === "function") await loadJobs();
    } else {
      alert("❌ Lỗi: " + data.message);
    }
  } catch (err) {
    alert("❌ Lỗi mạng: " + err.message);
  }
}

