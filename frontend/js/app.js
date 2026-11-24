"use strict";

const API_BASE_URL = "https://krmmk6s4hl.execute-api.ap-southeast-2.amazonaws.com/dev";

/* ------------------------------------------------------------------ *
 *  State
 * ------------------------------------------------------------------ */
const state = {
    students: [],        // full dataset from GET /students
    view: null,          // result of GET /students/search (null = not searching)
    sortKey: "created_at",
    sortDir: "desc",
    pendingDelete: null,
};

const PALETTE = ["#6366f1", "#8b5cf6", "#ec4899", "#f59e0b", "#10b981", "#06b6d4", "#ef4444", "#3b82f6"];

const $ = (id) => document.getElementById(id);

/* ------------------------------------------------------------------ *
 *  Tiny DOM helper (always textContent -> no HTML injection)
 * ------------------------------------------------------------------ */
function el(tag, props = {}, ...children) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(props)) {
        if (key === "class") node.className = value;
        else if (key === "style") node.style.cssText = value;
        else if (key === "dataset") Object.assign(node.dataset, value);
        else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
        else node.setAttribute(key, value);
    }
    for (const child of children.flat()) {
        if (child == null) continue;
        node.append(child.nodeType ? child : document.createTextNode(child));
    }
    return node;
}

const ICONS = {
    view:   '<circle cx="12" cy="12" r="3"/><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>',
    edit:   '<path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4z"/>',
    delete: '<polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>'
};

function icon(name) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.innerHTML = ICONS[name]; // static, trusted markup only
    return svg;
}

/* ------------------------------------------------------------------ *
 *  API layer
 * ------------------------------------------------------------------ */
async function api(path, { method = "GET", body } = {}) {
    let status = 0;

    try {
        const response = await fetch(API_BASE_URL + path, {
            method,
            headers: body ? { "Content-Type": "application/json" } : undefined,
            body: body ? JSON.stringify(body) : undefined
        });

        status = response.status;
        const text = await response.text();
        let data = {};
        try { data = text ? JSON.parse(text) : {}; } catch { data = { message: text }; }

        // The Lambda integration may return the whole proxy envelope
        // ({statusCode, headers, body: "<json string>"}) as the HTTP body.
        // Unwrap it so the real payload and real status are used.
        if (data && typeof data === "object" && "statusCode" in data && "body" in data) {
            status = Number(data.statusCode) || status;
            let inner = data.body;
            if (typeof inner === "string") {
                try { inner = JSON.parse(inner); } catch { inner = { message: inner }; }
            }
            data = inner ?? {};
        }

        if (status < 200 || status >= 300) {
            const err = new Error(data.message || data.error || `Request failed (${status})`);
            err.status = status;
            throw err;
        }
        setApiHealth(true);
        return data;
    } catch (error) {
        if (!error.status) {
            setApiHealth(false);
            error.message = "Network error — check your connection or API CORS settings.";
        }
        throw error;
    }
}

function setApiHealth(ok) {
    $("apiDot").className = "dot " + (ok ? "ok" : "bad");
    $("apiStatusText").textContent = ok ? "API Online" : "API Unreachable";
}

/* ------------------------------------------------------------------ *
 *  Data actions (each maps to an API Gateway route)
 * ------------------------------------------------------------------ */
function extractStudents(result) {
    if (Array.isArray(result)) return result;
    return result.students || result.items || result.data || [];
}

// GET /students
async function loadStudents({ silent = false } = {}) {
    state.view = null;
    if (!silent) renderSkeleton();
    try {
        const result = await api("/students");
        state.students = extractStudents(result);
    } catch (error) {
        state.students = [];
        toast(error.message, "error");
    }
    renderAll();
}

// GET /students/search?email=
async function searchByEmail(email) {
    $("apiSearchBtn").disabled = true;
    try {
        const result = await api(`/students/search?email=${encodeURIComponent(email)}`);
        state.view = extractStudents(result);
        toast(`Found ${state.view.length} match(es) for ${email}`, "success");
    } catch (error) {
        if (error.status === 404) {
            state.view = [];
            toast("No student found with that email.", "info");
        } else {
            toast(error.message, "error");
        }
    } finally {
        $("apiSearchBtn").disabled = false;
    }
    renderAll();
}

// GET /students/{id}
const fetchStudent = async (id) => {
    const result = await api(`/students/${encodeURIComponent(id)}`);
    return result.student || result.item || result;
};

// POST /students  or  PUT /students/{id}
async function saveStudent(event) {
    event.preventDefault();
    const id = $("studentId").value;
    const payload = {
        name: $("fName").value.trim(),
        email: $("fEmail").value.trim(),
        course: $("fCourse").value.trim()
    };

    if (!payload.name || !payload.email || !payload.course) return formError("All fields are required.");
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(payload.email)) return formError("Please enter a valid email address.");

    const submit = $("formSubmit");
    submit.disabled = true;
    submit.textContent = "Saving…";
    formError("");

    try {
        if (id) {
            await api(`/students/${encodeURIComponent(id)}`, { method: "PUT", body: payload });
            toast("Student updated successfully", "success");
        } else {
            await api("/students", { method: "POST", body: payload });
            toast("Student created successfully", "success");
        }
        closeModal("formModal");
        $("searchInput").value = "";
        await loadStudents({ silent: true });
    } catch (error) {
        formError(error.message);
    } finally {
        submit.disabled = false;
        submit.textContent = id ? "Save changes" : "Create student";
    }
}

// DELETE /students/{id}
async function confirmDelete() {
    const target = state.pendingDelete;
    if (!target) return;
    const btn = $("confirmBtn");
    btn.disabled = true;
    btn.textContent = "Deleting…";
    try {
        await api(`/students/${encodeURIComponent(target.student_id)}`, { method: "DELETE" });
        toast(`${target.name} deleted`, "success");
        closeModal("confirmModal");
        await loadStudents({ silent: true });
    } catch (error) {
        toast(error.message, "error");
    } finally {
        btn.disabled = false;
        btn.textContent = "Delete";
    }
}

/* ------------------------------------------------------------------ *
 *  Rendering
 * ------------------------------------------------------------------ */
function visibleStudents() {
    const source = state.view ?? state.students;
    const query = $("searchInput").value.trim().toLowerCase();
    const course = $("courseFilter").value;

    const rows = source.filter((s) =>
        (!course || s.course === course) &&
        (!query || [s.name, s.email, s.course, s.student_id].some((v) => String(v ?? "").toLowerCase().includes(query)))
    );

    const dir = state.sortDir === "asc" ? 1 : -1;
    return rows.sort((a, b) =>
        String(a[state.sortKey] ?? "").localeCompare(String(b[state.sortKey] ?? ""), undefined, { sensitivity: "base" }) * dir
    );
}

function renderAll() {
    renderStats();
    renderFilters();
    renderTable();
    renderChart();
}

function renderSkeleton() {
    $("resultMeta").textContent = "Loading…";
    $("tableBody").replaceChildren(...Array.from({ length: 5 }, () =>
        el("tr", {}, ...Array.from({ length: 5 }, () => el("td", {}, el("div", { class: "skeleton" }))))
    ));
}

function renderStats() {
    const list = state.students;
    const weekAgo = Date.now() - 7 * 864e5;
    $("statTotal").textContent = list.length;
    $("statCourses").textContent = new Set(list.map((s) => s.course).filter(Boolean)).size;
    $("statRecent").textContent = list.filter((s) => s.created_at && Date.parse(s.created_at) >= weekAgo).length;
}

function renderFilters() {
    const select = $("courseFilter");
    const current = select.value;
    const courses = [...new Set(state.students.map((s) => s.course).filter(Boolean))].sort();

    select.replaceChildren(el("option", { value: "" }, "All courses"), ...courses.map((c) => el("option", { value: c }, c)));
    select.value = courses.includes(current) ? current : "";
    $("courseList").replaceChildren(...courses.map((c) => el("option", { value: c })));
}

function renderTable() {
    const rows = visibleStudents();
    const body = $("tableBody");
    const total = (state.view ?? state.students).length;

    $("resultMeta").textContent = state.view
        ? `Showing ${rows.length} API search result(s)`
        : `Showing ${rows.length} of ${total} student${total === 1 ? "" : "s"}`;

    document.querySelectorAll("th[data-sort]").forEach((th) => {
        th.classList.toggle("asc", th.dataset.sort === state.sortKey && state.sortDir === "asc");
        th.classList.toggle("desc", th.dataset.sort === state.sortKey && state.sortDir === "desc");
    });

    if (!rows.length) {
        body.replaceChildren(el("tr", {}, el("td", { colspan: 5, class: "empty" },
            el("b", {}, state.students.length ? "No matching students" : "No students yet"),
            state.students.length ? "Try a different search or filter." : 'Click "Add Student" to get started.'
        )));
        return;
    }

    body.replaceChildren(...rows.map((s, i) => {
        const action = (name, title, cls = "") => el("button", { title, "aria-label": title, class: cls, dataset: { action: name, id: s.student_id } }, icon(name));
        return el("tr", { class: "row-in", style: `animation-delay:${Math.min(i, 12) * 25}ms` },
            el("td", {}, el("div", { class: "person" },
                avatar(s.name),
                el("div", {}, el("b", {}, s.name ?? "—"), el("small", {}, s.email ?? "—"))
            )),
            el("td", {}, el("span", { class: "sid" }, s.student_id ?? "—")),
            el("td", {}, el("span", { class: "badge" }, s.course ?? "—")),
            el("td", {}, el("span", { class: "date" }, formatDate(s.created_at))),
            el("td", { class: "right" }, el("div", { class: "row-actions" },
                action("view", "View profile"), action("edit", "Edit student"), action("delete", "Delete student", "del")
            ))
        );
    }));
}

function renderChart() {
    const counts = {};
    state.students.forEach((s) => { if (s.course) counts[s.course] = (counts[s.course] || 0) + 1; });
    const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 7);
    const chart = $("chart");

    if (!entries.length) {
        chart.replaceChildren(el("div", { class: "chart-empty" }, "No data to display yet."));
        return;
    }

    const max = entries[0][1];
    const fills = [];
    chart.replaceChildren(...entries.map(([course, count], i) => {
        const fill = el("div", { class: "bar-fill", style: `background:${PALETTE[i % PALETTE.length]}` });
        fills.push([fill, (count / max) * 100]);
        return el("div", { class: "bar-row" },
            el("div", { class: "bar-top" }, el("span", { title: course }, course), el("span", {}, count)),
            el("div", { class: "bar-track" }, fill)
        );
    }));
    requestAnimationFrame(() => requestAnimationFrame(() => fills.forEach(([f, w]) => (f.style.width = `${w}%`))));
}

function avatar(name = "?") {
    const initials = name.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0].toUpperCase()).join("") || "?";
    let hash = 0;
    for (const ch of name) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
    const c1 = PALETTE[hash % PALETTE.length];
    const c2 = PALETTE[(hash >> 3) % PALETTE.length];
    return el("div", { class: "avatar", style: `background:linear-gradient(135deg,${c1},${c2})` }, initials);
}

function formatDate(iso) {
    const d = iso ? new Date(iso) : null;
    return d && !isNaN(d) ? d.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" }) : "—";
}

/* ------------------------------------------------------------------ *
 *  Modals & toasts
 * ------------------------------------------------------------------ */
function openModal(id) { $(id).hidden = false; }
function closeModal(id) { $(id).hidden = true; }
function formError(msg) { $("formError").textContent = msg; }

function openForm(student = null) {
    $("formTitle").textContent = student ? "Edit Student" : "Add Student";
    $("formSubmit").textContent = student ? "Save changes" : "Create student";
    $("studentId").value = student?.student_id ?? "";
    $("fName").value = student?.name ?? "";
    $("fEmail").value = student?.email ?? "";
    $("fCourse").value = student?.course ?? "";
    formError("");
    openModal("formModal");
    setTimeout(() => $("fName").focus(), 50);
}

async function openEdit(id) {
    try {
        openForm(await fetchStudent(id)); // GET /students/{id} for fresh data
    } catch (error) {
        toast(error.message, "error");
    }
}

async function openProfile(id) {
    try {
        const s = await fetchStudent(id);
        const row = (k, v) => el("div", {}, el("span", {}, k), el("b", {}, v ?? "—"));
        const av = avatar(s.name);
        $("detailBody").replaceChildren(el("div", { class: "profile" },
            av,
            el("h3", {}, s.name ?? "—"),
            el("p", { class: "sub" }, s.course ?? "—"),
            el("div", { class: "kv" },
                row("Student ID", s.student_id),
                row("Email", s.email),
                row("Course", s.course),
                row("Created", s.created_at ? new Date(s.created_at).toLocaleString() : "—"),
                s.updated_at ? row("Last updated", new Date(s.updated_at).toLocaleString()) : null
            )
        ));
        openModal("detailModal");
    } catch (error) {
        toast(error.message, "error");
    }
}

function askDelete(id) {
    const s = state.students.find((x) => x.student_id === id) || (state.view || []).find((x) => x.student_id === id);
    if (!s) return;
    state.pendingDelete = s;
    $("confirmText").textContent = `This will permanently remove ${s.name} (${s.student_id}) from DynamoDB. This action cannot be undone.`;
    openModal("confirmModal");
}

function toast(message, type = "info", ms = 3200) {
    const node = el("div", { class: `toast ${type}` }, message);
    $("toasts").append(node);
    setTimeout(() => { node.classList.add("out"); setTimeout(() => node.remove(), 300); }, ms);
}

/* ------------------------------------------------------------------ *
 *  Theme
 * ------------------------------------------------------------------ */
function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem("theme", theme); } catch { /* storage unavailable */ }
}

/* ------------------------------------------------------------------ *
 *  Init
 * ------------------------------------------------------------------ */
document.addEventListener("DOMContentLoaded", () => {
    let saved = null;
    try { saved = localStorage.getItem("theme"); } catch { /* ignore */ }
    applyTheme(saved || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));

    $("themeToggle").addEventListener("click", () =>
        applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"));

    $("addBtn").addEventListener("click", () => openForm());
    $("refreshBtn").addEventListener("click", () => { $("searchInput").value = ""; loadStudents(); });
    $("studentForm").addEventListener("submit", saveStudent);
    $("confirmBtn").addEventListener("click", confirmDelete);

    // Live client-side filtering; Enter / button on a full email uses the search API.
    const isEmail = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
    const runSearch = () => {
        const q = $("searchInput").value.trim();
        if (isEmail(q)) searchByEmail(q);
        else if (!q) { if (state.view) { state.view = null; renderAll(); } }
        else toast("Enter a full email address to use the search API.", "info");
    };
    $("searchInput").addEventListener("input", () => {
        if (!$("searchInput").value.trim() && state.view) state.view = null;
        renderTable();
    });
    $("searchInput").addEventListener("keydown", (e) => { if (e.key === "Enter") runSearch(); });
    $("apiSearchBtn").addEventListener("click", runSearch);
    $("courseFilter").addEventListener("change", renderTable);

    document.querySelectorAll("th[data-sort]").forEach((th) => th.addEventListener("click", () => {
        const key = th.dataset.sort;
        state.sortDir = state.sortKey === key && state.sortDir === "asc" ? "desc" : "asc";
        state.sortKey = key;
        renderTable();
    }));

    // Row actions (event delegation).
    $("tableBody").addEventListener("click", (e) => {
        const btn = e.target.closest("button[data-action]");
        if (!btn) return;
        const { action, id } = btn.dataset;
        if (action === "view") openProfile(id);
        if (action === "edit") openEdit(id);
        if (action === "delete") askDelete(id);
    });

    // Modal close handling.
    document.querySelectorAll(".modal").forEach((modal) => {
        modal.addEventListener("click", (e) => { if (e.target === modal || e.target.closest("[data-close]")) modal.hidden = true; });
    });
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") document.querySelectorAll(".modal").forEach((m) => (m.hidden = true));
    });

    // Sidebar active-link highlighting.
    const links = [...document.querySelectorAll(".nav a")];
    links.forEach((a) => a.addEventListener("click", () => {
        links.forEach((l) => l.classList.toggle("active", l === a));
    }));
    loadStudents();
});
