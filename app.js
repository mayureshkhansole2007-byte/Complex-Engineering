/**
 * SmartPark - Frontend Application Controller
 * Connected directly to the Smart Parking Doubly Linked List backend engine.
 * Synchronizes with C++ & Python core via /api endpoints and parking_records.txt.
 */

const API_BASE = ""; // Relative URL, works seamlessly on any port/host

let currentCapacity = 20;
let cachedRecords = [];
let isRefreshing = false;

const $ = id => document.getElementById(id);

function escapeHTML(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[c]));
}

function showToast(message) {
  const toast = $("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.remove("show"), 3200);
}

function statusBadge(status) {
  const s = String(status || "").toUpperCase();
  const cls = s === "PARKED" ? "parked" : s === "COMPLETED" ? "completed" : "cancelled";
  return `<span class="status ${cls}">${escapeHTML(s)}</span>`;
}

function typeText(type) {
  return type === "2" ? "🏍 Two-wheeler" : "🚗 Four-wheeler";
}

function formatCurrency(val) {
  return `₹${Number(val || 0).toFixed(2)}`;
}

// -------------------------------------------------------------
// Navigation
// -------------------------------------------------------------
function navigate(page) {
  document.querySelectorAll(".page").forEach(el => {
    el.classList.toggle("active", el.id === `page-${page}`);
  });
  document.querySelectorAll(".nav-item").forEach(el => {
    el.classList.toggle("active", el.dataset.page === page);
  });

  const titles = {
    dashboard: "Dashboard",
    entry: "Vehicle Entry",
    exit: "Exit & Billing",
    vehicles: "Vehicle Records",
    reports: "Reports"
  };
  const titleEl = $("page-title");
  if (titleEl) titleEl.textContent = titles[page] || "Dashboard";

  // Trigger targeted refresh on navigation
  if (page === "reports") {
    fetchReport();
  } else if (page === "vehicles") {
    fetchRecords();
  }
}

document.querySelectorAll(".nav-item").forEach(btn => {
  btn.addEventListener("click", () => navigate(btn.dataset.page));
});

document.querySelectorAll("[data-go]").forEach(btn => {
  btn.addEventListener("click", () => navigate(btn.dataset.go));
});

// Set date chip
const dateChip = $("today-date");
if (dateChip) {
  dateChip.textContent = new Date().toLocaleDateString("en-IN", {
    weekday: "short",
    day: "2-digit",
    month: "short",
    year: "numeric"
  });
}

// -------------------------------------------------------------
// API Calls & Rendering
// -------------------------------------------------------------

async function fetchStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/status`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderStatus(data);
    updateConnectionIndicator(true);
  } catch (err) {
    console.warn("Status fetch failed:", err);
    updateConnectionIndicator(false);
  }
}

async function fetchRecords() {
  try {
    const res = await fetch(`${API_BASE}/api/records`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const records = await res.json();
    cachedRecords = records;
    renderRecordsTable();
    renderRecentTable(records.filter(r => r.status === "PARKED"));
  } catch (err) {
    console.warn("Records fetch failed:", err);
  }
}

async function fetchReport() {
  try {
    const res = await fetch(`${API_BASE}/api/report`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const rep = await res.json();
    renderReport(rep);
  } catch (err) {
    console.warn("Report fetch failed:", err);
  }
}

function updateConnectionIndicator(online) {
  const dot = $("system-dot");
  const title = $("system-status-title");
  const desc = $("system-status-desc");

  if (online) {
    if (dot) dot.className = "status-dot";
    if (title) title.textContent = "System Connected";
    if (desc) desc.textContent = "Doubly Linked List Backend";
  } else {
    if (dot) dot.className = "status-dot offline";
    if (title) title.textContent = "Offline Mode";
    if (desc) desc.textContent = "Start server.py to sync";
  }
}

function renderStatus(data) {
  currentCapacity = data.capacity || 20;

  // Stat Counters
  const occupiedEl = $("occupied-count");
  if (occupiedEl) {
    occupiedEl.innerHTML = `${data.occupied} <small>/ ${data.capacity}</small>`;
  }

  const availableEl = $("available-count");
  if (availableEl) {
    availableEl.textContent = data.available;
  }

  const badgeEl = $("capacity-badge");
  if (badgeEl) {
    badgeEl.textContent = `${data.capacity} total slots`;
  }

  // Demo pill
  const pillEl = $("demo-pill");
  if (pillEl) {
    pillEl.textContent = data.demo_mode ? "SIMULATION MODE (1s = 1m)" : "REALTIME MODE";
  }

  // Render Slots Grid
  const slotGrid = $("slot-grid");
  if (!slotGrid) return;

  const slotItems = (data.slots || []).map(s => {
    const isOcc = s.is_occupied;
    const v = s.vehicle;
    const symbol = isOcc ? (v.type === "2" ? "🏍" : "🚗") : "＋";
    const label = isOcc ? escapeHTML(v.registration) : "Available";
    const sub = isOcc ? `Slot ${s.slot} • ${v.est_charge ? '₹' + v.est_charge : 'Active'}` : `Slot ${s.slot}`;
    const clickAttr = isOcc 
      ? `onclick="selectVehicleForExit('${escapeHTML(v.registration)}')"` 
      : `onclick="navigate('entry')"`;

    return `
      <div class="slot ${isOcc ? 'occupied' : 'available'}" ${clickAttr} title="${isOcc ? 'Click to process exit for ' + v.registration : 'Click to register vehicle'}">
        <span class="slot-symbol">${symbol}</span>
        <b>Slot ${s.slot}</b>
        <small>${label}</small>
      </div>
    `;
  });

  slotGrid.innerHTML = slotItems.join("");
}

function renderRecentTable(parkedList) {
  const tbody = $("recent-table");
  if (!tbody) return;

  if (!parkedList || parkedList.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:24px;color:#9aa3b2;">No vehicles currently parked.</td></tr>`;
    return;
  }

  tbody.innerHTML = parkedList.map(v => `
    <tr>
      <td class="reg">${escapeHTML(v.registration)}</td>
      <td><span class="type-label">${typeText(v.type)}</span></td>
      <td><b>Slot ${v.slot}</b></td>
      <td>${escapeHTML(v.entry_time_str || "Active")}</td>
      <td>
        <span style="display:inline-flex;gap:6px;align-items:center;">
          ${statusBadge(v.status)}
          <button class="text-button" onclick="selectVehicleForExit('${escapeHTML(v.registration)}')" style="font-size:10px;text-decoration:underline;">Exit ↗</button>
        </span>
      </td>
    </tr>
  `).join("");
}

function renderRecordsTable() {
  const tbody = $("records-table");
  const totalBadge = $("record-total");
  if (!tbody) return;

  const query = ($("search-input")?.value || "").trim().toUpperCase();
  const filtered = cachedRecords.filter(v =>
    (v.registration || "").toUpperCase().includes(query) ||
    String(v.slot || "").includes(query)
  );

  if (totalBadge) {
    totalBadge.textContent = `${filtered.length} record${filtered.length === 1 ? "" : "s"}`;
  }

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:24px;color:#9aa3b2;">No matching records found.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(v => `
    <tr>
      <td class="reg">${escapeHTML(v.registration)}</td>
      <td><span class="type-label">${typeText(v.type)}</span></td>
      <td>${v.slot ? `Slot ${v.slot}` : "—"}</td>
      <td>${escapeHTML(v.entry_time_str || "—")}</td>
      <td><b>${formatCurrency(v.charge)}</b></td>
      <td>${statusBadge(v.status)}</td>
    </tr>
  `).join("");
}

function renderReport(rep) {
  const exitEl = $("exit-count");
  const revEl = $("revenue-count");
  if (exitEl) exitEl.textContent = rep.exits_today ?? 0;
  if (revEl) revEl.textContent = formatCurrency(rep.total_revenue ?? 0);

  const repEntries = $("report-entries");
  const repExits = $("report-exits");
  const repCancel = $("report-cancel");
  const repRev = $("report-revenue");

  if (repEntries) repEntries.textContent = rep.entries_today ?? 0;
  if (repExits) repExits.textContent = rep.exits_today ?? 0;
  if (repCancel) repCancel.textContent = rep.cancellations_today ?? 0;
  if (repRev) repRev.textContent = formatCurrency(rep.total_revenue ?? 0);
}

window.selectVehicleForExit = function(reg) {
  navigate("exit");
  const exitInput = $("exit-registration");
  if (exitInput) {
    exitInput.value = reg;
    exitInput.focus();
  }
};

async function refreshAll() {
  if (isRefreshing) return;
  isRefreshing = true;
  try {
    await Promise.all([fetchStatus(), fetchRecords(), fetchReport()]);
  } finally {
    isRefreshing = false;
  }
}

// -------------------------------------------------------------
// Form Submissions
// -------------------------------------------------------------

$("entry-form")?.addEventListener("submit", async event => {
  event.preventDefault();
  const regInput = $("registration");
  const registration = (regInput?.value || "").trim().toUpperCase();
  const typeOption = document.querySelector('input[name="type"]:checked');
  const type = typeOption ? typeOption.value : "4";

  if (!registration || registration.includes("|")) {
    return showToast("Enter a valid registration number (no '|' characters).");
  }

  try {
    const res = await fetch(`${API_BASE}/api/entry`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ registration, type })
    });

    const data = await res.json();

    if (res.ok && data.success) {
      showToast(`Success: ${registration} assigned to Slot ${data.slot}!`);
      event.currentTarget.reset();
      await refreshAll();
      navigate("dashboard");
    } else {
      showToast(data.message || "Failed to register vehicle.");
    }
  } catch (err) {
    console.error("Entry error:", err);
    showToast("Network error: Could not reach the parking engine.");
  }
});

$("exit-form")?.addEventListener("submit", async event => {
  event.preventDefault();
  const regInput = $("exit-registration");
  const registration = (regInput?.value || "").trim().toUpperCase();

  if (!registration) {
    return showToast("Enter a vehicle registration number.");
  }

  try {
    const res = await fetch(`${API_BASE}/api/exit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ registration })
    });

    const data = await res.json();
    const resultBox = $("bill-result");

    if (res.ok && data.success && data.bill) {
      const b = data.bill;
      resultBox.classList.remove("hidden");
      resultBox.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
          <h3 style="margin:0;">Parking Receipt & Bill</h3>
          <span class="status completed">COMPLETED</span>
        </div>
        <div class="bill-row"><span>Vehicle Registration</span><b>${escapeHTML(b.registration)}</b></div>
        <div class="bill-row"><span>Vehicle Type</span><b>${typeText(b.type)}</b></div>
        <div class="bill-row"><span>Parking Slot</span><b>Slot ${b.slot}</b></div>
        <div class="bill-row"><span>Entry Time</span><b>${escapeHTML(b.entry_time_str)}</b></div>
        <div class="bill-row"><span>Exit Time</span><b>${escapeHTML(b.exit_time_str)}</b></div>
        <div class="bill-row"><span>Chargeable Duration</span><b>${b.chargeable_hours} hour${b.chargeable_hours > 1 ? "s" : ""}</b></div>
        <div class="bill-row"><span>Hourly Rate</span><b>₹${b.hourly_rate} / hr</b></div>
        <div class="bill-row total"><span>Total Bill Paid</span><b>${formatCurrency(b.charge)}</b></div>
        <div style="margin-top:16px;display:flex;gap:10px;">
          <button type="button" class="btn secondary" onclick="window.print()">🖨 Print Receipt</button>
          <button type="button" class="btn primary" onclick="document.getElementById('bill-result').classList.add('hidden')">Done</button>
        </div>
      `;

      showToast(`Exit processed for ${registration}. Bill: ${formatCurrency(b.charge)}`);
      await refreshAll();
    } else {
      resultBox.classList.add("hidden");
      showToast(data.message || `No active parked vehicle found for '${registration}'.`);
    }
  } catch (err) {
    console.error("Exit error:", err);
    showToast("Network error: Could not reach the parking engine.");
  }
});

// Search input debounce/live filtering
$("search-input")?.addEventListener("input", () => {
  renderRecordsTable();
});

// Initialize on page load
refreshAll();

// Auto-refresh every 3 seconds to keep UI synchronized with C++ console actions
setInterval(refreshAll, 3000);
