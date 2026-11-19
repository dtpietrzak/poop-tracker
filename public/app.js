(() => {
  "use strict";

  const STORAGE_KEY = "poop-tracker:v1";

  // ---- Storage -------------------------------------------------------------
  // Shape: { onboarded: boolean, poops: { "YYYY-MM-DD": true } }
  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return { onboarded: false, poops: {} };
      const parsed = JSON.parse(raw);
      return {
        onboarded: parsed.onboarded === true,
        poops: parsed.poops && typeof parsed.poops === "object" ? parsed.poops : {},
      };
    } catch {
      return { onboarded: false, poops: {} };
    }
  }

  function saveState() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (err) {
      console.error("Could not save poop state", err);
    }
  }

  const state = loadState();

  // ---- Helpers -------------------------------------------------------------
  const pad = (n) => String(n).padStart(2, "0");
  const dateKey = (y, m, d) => `${y}-${pad(m + 1)}-${pad(d)}`;
  const monthFmt = new Intl.DateTimeFormat(undefined, { month: "long", year: "numeric" });
  const longFmt = new Intl.DateTimeFormat(undefined, { weekday: "long", month: "long", day: "numeric" });

  const $ = (id) => document.getElementById(id);
  const grid = $("cal-grid");
  const monthLabel = $("month-label");
  const monthCount = $("month-count");

  const now = new Date();
  let viewYear = now.getFullYear();
  let viewMonth = now.getMonth();

  // ---- Calendar ------------------------------------------------------------
  function render(popKey) {
    const today = new Date();
    const todayKey = dateKey(today.getFullYear(), today.getMonth(), today.getDate());
    const firstWeekday = new Date(viewYear, viewMonth, 1).getDay();
    const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();

    monthLabel.textContent = monthFmt.format(new Date(viewYear, viewMonth, 1));
    grid.replaceChildren();

    for (let i = 0; i < firstWeekday; i++) {
      const blank = document.createElement("div");
      blank.className = "day empty";
      grid.appendChild(blank);
    }

    let count = 0;
    for (let d = 1; d <= daysInMonth; d++) {
      const key = dateKey(viewYear, viewMonth, d);
      const pooped = !!state.poops[key];
      if (pooped) count++;

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "day";
      btn.dataset.key = key;
      btn.dataset.day = d;
      if (key === todayKey) btn.classList.add("today");
      if (pooped) btn.classList.add("pooped");
      if (key === popKey) btn.classList.add("pop");
      btn.textContent = pooped ? "💩" : d;
      const label = longFmt.format(new Date(viewYear, viewMonth, d));
      btn.setAttribute("aria-label", pooped ? `${label}, pooped` : label);
      btn.setAttribute("aria-pressed", String(pooped));
      grid.appendChild(btn);
    }

    monthCount.textContent =
      count === 0 ? "No poops yet this month" : `${count} poop${count === 1 ? "" : "s"} this month`;
  }

  grid.addEventListener("click", (e) => {
    const btn = e.target.closest(".day:not(.empty)");
    if (!btn) return;
    const key = btn.dataset.key;
    if (state.poops[key]) {
      openConfirm(key);
    } else {
      state.poops[key] = true;
      saveState();
      render(key);
    }
  });

  $("prev-month").addEventListener("click", () => shiftMonth(-1));
  $("next-month").addEventListener("click", () => shiftMonth(1));
  $("today-btn").addEventListener("click", () => {
    const t = new Date();
    viewYear = t.getFullYear();
    viewMonth = t.getMonth();
    render();
  });

  function shiftMonth(delta) {
    const d = new Date(viewYear, viewMonth + delta, 1);
    viewYear = d.getFullYear();
    viewMonth = d.getMonth();
    render();
  }

  // ---- Remove confirmation -------------------------------------------------
  const confirmModal = $("confirm-modal");
  let pendingKey = null;
  let lastFocus = null;

  function openConfirm(key) {
    pendingKey = key;
    lastFocus = document.activeElement;
    const [y, m, d] = key.split("-").map(Number);
    $("confirm-text").textContent = `This will remove the poop logged on ${longFmt.format(new Date(y, m - 1, d))}.`;
    confirmModal.hidden = false;
    $("confirm-cancel").focus();
  }

  function closeConfirm() {
    confirmModal.hidden = true;
    pendingKey = null;
    if (lastFocus) lastFocus.focus();
  }

  $("confirm-cancel").addEventListener("click", closeConfirm);
  $("confirm-ok").addEventListener("click", () => {
    if (pendingKey) {
      delete state.poops[pendingKey];
      saveState();
      render();
    }
    closeConfirm();
  });
  confirmModal.addEventListener("click", (e) => {
    if (e.target === confirmModal) closeConfirm();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !confirmModal.hidden) closeConfirm();
  });

  // ---- Onboarding ----------------------------------------------------------
  const onboarding = $("onboarding");
  const steps = onboarding.querySelectorAll(".onb-step");

  function showStep(n) {
    steps.forEach((s) => (s.hidden = s.dataset.step !== String(n)));
    const btn = onboarding.querySelector(`.onb-step[data-step="${n}"] .btn`);
    if (btn) btn.focus();
  }

  if (!state.onboarded) {
    onboarding.hidden = false;
    showStep(1);
  }

  $("onb-continue").addEventListener("click", () => showStep(2));
  $("onb-done").addEventListener("click", () => {
    state.onboarded = true;
    saveState();
    onboarding.hidden = true;
  });

  // ---- Keep "today" fresh if the app stays open past midnight -------------
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") render();
  });

  render();

  // ---- PWA -----------------------------------------------------------------
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("sw.js").catch((err) => console.warn("SW registration failed", err));
    });
  }
})();
