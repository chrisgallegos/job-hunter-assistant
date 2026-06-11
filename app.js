// Job Hunter Toolkit — app.js
// Vanilla JS. No dependencies. Reads/writes localStorage.
// MD export triggers a browser download dialog.

const STORAGE_KEY = 'jht_narrative';
const TRACKER_KEY = 'jht_tracker';
const JD_KEY      = 'jht_jd';

// ─── Navigation ───────────────────────────────────────────

function showSection(id) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  document.querySelector(`[data-section="${id}"]`)?.classList.add('active');
}

// ─── Career Narrative Wizard ───────────────────────────────

const STEPS = [
  {
    id: 'target',
    label: 'Step 1 of 7 — What you want',
    question: "What kind of role are you looking for?",
    hint: "Think beyond titles — what does the right job actually feel like? Broad or specialized? Leading a team or individual contributor? Any industries you're drawn to or avoiding?",
    fields: [
      { key: 'target_roles',    label: 'Target roles',              type: 'text',     placeholder: 'Senior Designer, Senior Art Director...' },
      { key: 'seniority',       label: 'Seniority',                 type: 'text',     placeholder: 'Senior IC, open to lead' },
      { key: 'industries',      label: 'Industries (drawn to / avoiding)', type: 'textarea', placeholder: 'Gaming and entertainment first. Open to agencies...' },
    ]
  },
  {
    id: 'logistics',
    label: 'Step 2 of 7 — Logistics',
    question: "Location, salary, deal-breakers.",
    hint: "Be honest here — this file is private. Vague targets produce vague searches. Name the salary number you need. Deal-breakers are patterns from past experience, not hypotheticals.",
    fields: [
      { key: 'location',      label: 'Location / remote',  type: 'text',     placeholder: 'Remote or Seattle area' },
      { key: 'salary',        label: 'Salary floor',       type: 'text',     placeholder: '$150k FTE. $110k for gaming specifically.' },
      { key: 'dealbreakers',  label: 'Deal-breakers',      type: 'textarea', placeholder: 'Micromanaging leadership. Startups without strong experienced leadership...' },
    ]
  },
  {
    id: 'hero',
    label: 'Step 3 of 7 — Your hero statement',
    question: "Who are you professionally, in two sentences?",
    hint: "Not a job title — the thing underneath the titles. What you're great at, what makes you different. This becomes the spine of every cover letter and the answer to 'tell me about yourself.' Write it, then read it out loud.",
    fields: [
      { key: 'hero', label: 'Hero statement', type: 'textarea', placeholder: 'Senior product designer, nearly 20 years, generalist by conviction...' },
    ]
  },
  {
    id: 'skills',
    label: 'Step 4 of 7 — Skills inventory',
    question: "What would you bet on in an interview — and what wouldn't you lead with?",
    hint: "Two honest lists. Core strengths: things you'd put front and center. Working knowledge: things you can do but wouldn't claim professional-grade. The split matters more than the length.",
    fields: [
      { key: 'core_strengths',    label: 'Core strengths',   type: 'textarea', placeholder: 'Visual design leadership, art direction, production discipline...' },
      { key: 'working_knowledge', label: 'Working knowledge', type: 'textarea', placeholder: 'Motion design, 3D, game engines, illustration...' },
    ]
  },
  {
    id: 'projects',
    label: 'Step 5 of 7 — Key projects',
    question: "What are your 3–6 strongest projects?",
    hint: "For each one: what was at stake, what was specifically yours, what decision you made and why, what changed because of it. Numbers if you have them. Write loosely — you can refine later.",
    fields: [
      { key: 'projects', label: 'Projects (one per paragraph, or bullet per project)', type: 'textarea', placeholder: 'TOYS — Masterbrand, 2024-2026. Designed the GenAI kitchen visualization feature. Account wall conversion 23% → 33%...\n\nAdinovis audit platform — 100+ hour workflow reduced to ~10...' },
    ]
  },
  {
    id: 'arc',
    label: 'Step 6 of 7 — Career arc',
    question: "Walk me through your career — not the resume, the why.",
    hint: "Each move: what happened, what you chose, what you learned. The moves that need explaining are the ones worth writing down. Layoffs, departures, pivots. Don't apologize — find the honest framing.",
    fields: [
      { key: 'arc', label: 'Career arc', type: 'textarea', placeholder: 'Started at Art Institute, first pro role at Provis Media...' },
    ]
  },
  {
    id: 'transition',
    label: 'Step 7 of 7 — The transition story',
    question: "Why are you searching right now?",
    hint: "One paragraph you can say out loud without flinching. Frame it as movement toward something, not away from something. Add a note on how to calibrate it per audience type if useful.",
    fields: [
      { key: 'transition', label: 'Transition story', type: 'textarea', placeholder: 'I was recruited specifically out of [company] by a VP building a team with a clear vision...' },
      { key: 'voice',      label: 'Voice notes (cover letters + outreach)', type: 'textarea', placeholder: 'Short. Biz casual. Calm confidence. No em dashes — colons instead...' },
    ]
  }
];

let currentStep = 0;
let narrativeData = {};

function loadNarrative() {
  try { narrativeData = JSON.parse(localStorage.getItem(STORAGE_KEY)) || {}; }
  catch { narrativeData = {}; }
}

function saveNarrative() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(narrativeData));
}

function hasNarrativeContent() {
  const keys = ['hero','target_roles','projects','arc','transition'];
  return keys.some(k => narrativeData[k] && narrativeData[k].trim().length > 0);
}

function showNarrativeSection() {
  if (hasNarrativeContent()) {
    renderPortrait();
  } else {
    document.getElementById('portrait-view').style.display = 'none';
    document.getElementById('wizard-container').style.display = 'block';
    renderWizard();
  }
}

function renderPortrait() {
  const d = narrativeData;
  const portrait = document.getElementById('portrait-view');
  const wizard   = document.getElementById('wizard-container');

  wizard.style.display = 'none';
  portrait.style.display = 'block';

  const metaRows = [
    ['Target roles',  d.target_roles],
    ['Seniority',     d.seniority],
    ['Industries',    d.industries],
    ['Location',      d.location],
    ['Salary floor',  d.salary],
    ['Deal-breakers', d.dealbreakers],
  ].filter(([,v]) => v && v.trim())
   .map(([k,v]) => `
    <div class="portrait-meta-row">
      <span class="portrait-meta-key">${k}</span>
      <span class="portrait-meta-val">${escHtml(v)}</span>
    </div>`).join('');

  const projectBlocks = d.projects
    ? d.projects.split(/\n{2,}/).filter(p => p.trim()).map(p =>
        `<div class="portrait-project">${escHtml(p.trim())}</div>`
      ).join('')
    : '<div class="portrait-project text-muted">Not yet filled in.</div>';

  portrait.innerHTML = `
    <div class="portrait">

      ${d.hero ? `
      <div class="portrait-hero">
        <div class="portrait-label">Hero statement</div>
        <p>${escHtml(d.hero)}</p>
      </div>` : ''}

      ${metaRows ? `
      <div class="portrait-block">
        <div class="portrait-label">Looking for</div>
        <div class="portrait-meta">${metaRows}</div>
      </div>` : ''}

      ${(d.core_strengths || d.working_knowledge) ? `
      <div class="portrait-block">
        <div class="portrait-label">Skills</div>
        <div class="portrait-skills">
          ${d.core_strengths ? `
          <div class="portrait-skills-group">
            <div class="portrait-skills-group-label">Core strengths</div>
            <div class="portrait-skills-group-val">${escHtml(d.core_strengths)}</div>
          </div>` : ''}
          ${d.working_knowledge ? `
          <div class="portrait-skills-group">
            <div class="portrait-skills-group-label">Working knowledge</div>
            <div class="portrait-skills-group-val">${escHtml(d.working_knowledge)}</div>
          </div>` : ''}
        </div>
      </div>` : ''}

      ${d.projects ? `
      <div class="portrait-block">
        <div class="portrait-label">Key projects</div>
        <div class="portrait-projects">${projectBlocks}</div>
      </div>` : ''}

      ${d.arc ? `
      <div class="portrait-block">
        <div class="portrait-label">Career arc</div>
        <div class="portrait-body">${escHtml(d.arc)}</div>
      </div>` : ''}

      ${d.transition ? `
      <div class="portrait-block">
        <div class="portrait-label">Transition story</div>
        <div class="portrait-transition">${escHtml(d.transition)}</div>
      </div>` : ''}

      ${d.voice ? `
      <div class="portrait-block">
        <div class="portrait-label">Voice</div>
        <div class="portrait-body text-muted">${escHtml(d.voice)}</div>
      </div>` : ''}

      <div class="portrait-actions">
        <button class="btn btn-primary" onclick="editNarrative()">Edit or add to this →</button>
        <button class="btn btn-ghost" onclick="exportNarrativeMD()">Export MD</button>
        <button class="btn btn-ghost portrait-danger" onclick="confirmRestart()">Start over</button>
      </div>

    </div>
  `;
}

function editNarrative() {
  document.getElementById('portrait-view').style.display = 'none';
  document.getElementById('wizard-container').style.display = 'block';
  currentStep = 0;
  renderWizard();
}

function confirmRestart() {
  if (confirm('Clear your narrative and start over from question 1? This cannot be undone.')) {
    narrativeData = {};
    localStorage.removeItem(STORAGE_KEY);
    currentStep = 0;
    document.getElementById('portrait-view').style.display = 'none';
    document.getElementById('wizard-container').style.display = 'block';
    renderWizard();
    // Reset home CTA
    const startBtn = document.getElementById('start-btn');
    if (startBtn) startBtn.textContent = 'Start my narrative →';
  }
}

function escHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderWizard() {
  const container = document.getElementById('wizard-container');
  container.innerHTML = '';

  // Progress bar
  const progress = document.createElement('div');
  progress.className = 'wizard-progress';
  STEPS.forEach((_, i) => {
    const pip = document.createElement('div');
    pip.className = 'progress-step' + (i < currentStep ? ' done' : i === currentStep ? ' current' : '');
    progress.appendChild(pip);
  });
  container.appendChild(progress);

  // Steps
  STEPS.forEach((step, i) => {
    const div = document.createElement('div');
    div.className = 'wizard-step' + (i === currentStep ? ' active' : '');

    let fieldsHtml = step.fields.map(f => `
      <div class="field">
        <label for="field_${f.key}">${f.label}</label>
        ${f.type === 'textarea'
          ? `<textarea id="field_${f.key}" name="${f.key}" rows="5" placeholder="${f.placeholder}">${narrativeData[f.key] || ''}</textarea>`
          : `<input type="text" id="field_${f.key}" name="${f.key}" placeholder="${f.placeholder}" value="${narrativeData[f.key] || ''}">`
        }
      </div>
    `).join('');

    div.innerHTML = `
      <div class="step-label">${step.label}</div>
      <div class="step-question">${step.question}</div>
      <div class="step-hint">${step.hint}</div>
      ${fieldsHtml}
      <div class="wizard-actions">
        <button class="btn btn-ghost" onclick="wizardBack()" ${i === 0 ? 'disabled' : ''}>← Back</button>
        <div class="wizard-actions-right">
          <button class="btn btn-ghost btn-sm" onclick="wizardSave()">Save progress</button>
          ${i < STEPS.length - 1
            ? `<button class="btn btn-primary" onclick="wizardNext()">Continue →</button>`
            : `<button class="btn btn-accent" onclick="wizardFinish()">Export narrative →</button>`
          }
        </div>
      </div>
    `;
    container.appendChild(div);
  });
}

function collectCurrentStep() {
  const step = STEPS[currentStep];
  step.fields.forEach(f => {
    const el = document.getElementById(`field_${f.key}`);
    if (el) narrativeData[f.key] = el.value.trim();
  });
  saveNarrative();
}

function wizardNext() {
  collectCurrentStep();
  if (currentStep < STEPS.length - 1) {
    currentStep++;
    renderWizard();
    window.scrollTo(0, 0);
  }
}

function wizardBack() {
  collectCurrentStep();
  if (currentStep > 0) {
    currentStep--;
    renderWizard();
    window.scrollTo(0, 0);
  }
}

function wizardSave() {
  collectCurrentStep();
  const btn = event.target;
  btn.textContent = 'Saved ✓';
  setTimeout(() => btn.textContent = 'Save progress', 1500);
}

function wizardFinish() {
  collectCurrentStep();
  exportNarrativeMD();
}

function exportNarrativeMD() {
  const d = narrativeData;
  const md = `# Career Narrative

## Hero statement

${d.hero || '[Not yet filled in]'}

## What I'm looking for

- **Target roles:** ${d.target_roles || '[Fill in]'}
- **Seniority:** ${d.seniority || '[Fill in]'}
- **Industries:** ${d.industries || '[Fill in]'}
- **Location / remote:** ${d.location || '[Fill in]'}
- **Salary floor:** ${d.salary || '[Fill in]'}
- **Deal-breakers:** ${d.dealbreakers || '[Fill in]'}

## Skills inventory

**Core strengths:** ${d.core_strengths || '[Fill in]'}

**Working knowledge:** ${d.working_knowledge || '[Fill in]'}

## Key projects

${d.projects || '[Fill in — one project per paragraph: context, role, what you did, outcome/metrics]'}

## Career arc

${d.arc || '[Fill in]'}

## The transition story

${d.transition || '[Fill in]'}

## Voice — cover letters and outreach

${d.voice || '[Fill in your voice rules]'}

---

*Generated by Job Hunter Toolkit — https://github.com/[your-handle]/job-hunter-toolkit*
`;
  downloadFile('career-narrative.md', md);
}

// ─── Jobs (scraper view) ───────────────────────────────────
// Talks to serve.py's API. Without the server (file:// or plain static
// hosting) the section degrades to instructions for starting it.

let jobsData = [];
let jobsInitialized = false;
let verdicts = {};

async function initJobs() {
  if (jobsInitialized) return;
  try {
    const [jobsResp, verdictsResp] = await Promise.all([
      fetch('/api/jobs'),
      fetch('/api/verdicts'),
    ]);
    if (!jobsResp.ok) throw new Error(jobsResp.status);
    const data = await jobsResp.json();
    jobsInitialized = true;
    jobsData = data.postings || [];

    // Load verdicts and merge into each posting
    if (verdictsResp.ok) {
      verdicts = await verdictsResp.json();
      jobsData.forEach(posting => {
        if (verdicts[posting.url]) {
          posting.verdict = verdicts[posting.url];
        }
      });
    }

    renderJobs(data.generated
      ? `Last scan: ${data.generated} — ${jobsData.length} posting(s).`
      : 'No scans yet. Hit "Scan now" to pull fresh postings.');
    loadWatchlistText();
  } catch {
    document.getElementById('jobs-offline').style.display = 'block';
    document.getElementById('scan-btn').disabled = true;
  }
}

async function runScan() {
  const btn = document.getElementById('scan-btn');
  const status = document.getElementById('jobs-status');
  btn.disabled = true;
  btn.textContent = 'Scanning…';
  status.textContent = 'Checking company boards — this takes a moment; the scraper is polite to their APIs.';
  try {
    const resp = await fetch('/api/scrape', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        days: parseInt(document.getElementById('scan-days').value, 10),
        rescan: document.getElementById('scan-rescan').checked,
      }),
    });
    const data = await resp.json();
    if (data.error) {
      renderJobs(data.error);
    } else {
      jobsData = data.postings || [];
      renderJobs(data.new > 0
        ? `${data.new} new matching posting(s). Saved to private/jobs/.`
        : 'No new matching postings in that window. Widen the days, tick "include seen," or add companies to the watchlist.');
    }
  } catch {
    renderJobs('Scan failed — is the server still running?');
  }
  btn.disabled = false;
  btn.textContent = 'Scan now →';
}

function combinedScore(j) {
  return j.score + (j.verdict ? j.verdict.delta : 0);
}

// AI-FLAVOR: the verdict attribution label is "your AI says" — change it to match
// your assistant's name or voice. Search this file for "your AI says" to find it.
// Examples: "Claude thinks", "Gemini's take", "GPT says", "your assistant says".
function scoreCol(j) {
  const note = j.verdict && j.verdict.why
    ? `Keyword score ${j.score}${j.verdict.delta ? `, ${j.verdict.delta > 0 ? '+' : '−'}${Math.abs(j.verdict.delta)} from your AI` : ''}: ${j.verdict.why}`
    : 'Keyword score from your watchlist. Run your AI over private/jobs/review-queue.md to add a judgment layer.';

  let deltaHtml = '';
  if (j.verdict && j.verdict.delta !== 0) {
    const d = j.verdict.delta;
    const cls = d > 0 ? 'up' : 'down';
    const sign = d > 0 ? '+' : '−';
    deltaHtml = `<em class="job-score-delta ${cls}">${sign}${Math.abs(d)}</em>`;
  }

  return `<div class="job-score-col" title="${escHtml(note)}">
    <span class="job-score-num">${j.score}</span>
    ${deltaHtml}
  </div>`;
}

function extractExcerpt(desc) {
  if (!desc) return null;
  // Split into paragraphs, skip short/boilerplate openers
  const paras = desc.split(/\n+/).map(p => p.trim()).filter(p => p.length > 60);
  const text = paras[0] || desc.trim();
  // Strip markdown-ish artifacts
  return text.replace(/[#*_`>]/g, '').replace(/\s+/g, ' ').trim();
}

function extractSalary(desc) {
  if (!desc) return null;
  const m = desc.match(/\$[\d,]+(?:[kK])?\s*(?:[-–—]\s*\$[\d,]+(?:[kK])?)?(?:\s*(?:\/yr|\/year|annually|\/hr|\/hour|per year|per hour))?/);
  if (!m || !m[0].includes('$')) return null;
  const raw = m[0].trim();
  return raw.length > 60 ? raw.slice(0, 60) + '…' : raw;
}

function extractEmploymentType(desc) {
  if (!desc) return null;
  const m = desc.match(/\b(full[- ]time|part[- ]time|contract|freelance|temporary)\b/i);
  return m ? m[1].toLowerCase().replace('-', ' ') : null;
}

function renderJobs(statusMsg) {
  document.getElementById('jobs-status').textContent = statusMsg || '';
  jobsData.sort((a, b) => combinedScore(b) - combinedScore(a));
  const list = document.getElementById('jobs-list');
  list.innerHTML = jobsData.map((j, i) => {
    const salary = extractSalary(j.description);
    const locParts = [j.location ? escHtml(j.location) : null, j.remote ? '<strong>remote</strong>' : null].filter(Boolean).join(' · ');
    const locWithSalary = [locParts, salary ? `<span class="job-card-salary-inline">${escHtml(salary)}</span>` : null].filter(Boolean).join(' · ');
    const excerpt = extractExcerpt(j.description);
    const chips = j.chips || [];

    return `
    <div class="job-card">
      <div class="job-card-body">
        <div class="job-card-identity">
          <div class="job-card-title">${escHtml(j.title)}</div>
          <div class="job-card-company">
            <span class="job-card-co-name">${escHtml(j.company)}</span>
          </div>
          <div class="job-card-location-row">
            ${locWithSalary ? `<span class="job-card-location">${locWithSalary}</span>` : ''}
            <span class="job-card-provenance">${j.posted ? j.posted : 'Undated'} · ${escHtml(j.source)}</span>
          </div>
        </div>
        ${excerpt ? `<div class="job-card-excerpt">${escHtml(excerpt)}</div>` : ''}
        ${j.verdict && j.verdict.why ? `<div class="job-card-verdict"><em class="job-card-verdict-attr">Claude's read</em>${escHtml(j.verdict.why)}</div>` : ''}
        <div class="job-card-actions">
          <button class="job-icon-btn" onclick="trackJob(${i})" title="Track this posting" aria-label="Track">
            <span class="material-symbols-rounded">bookmark_add</span>
          </button>
          <button class="job-icon-btn job-dismiss" onclick="dismissJob(${i})" title="Dismiss" aria-label="Dismiss">
            <span class="material-symbols-rounded">close</span>
          </button>
        </div>
        ${chips.length ? `<div class="job-card-chips">${chips.map(c => `<span class="job-card-chip">${escHtml(c)}</span>`).join('')}</div>` : ''}
      </div>
      ${scoreCol(j)}
      <div class="job-card-action-bar">
        <a class="job-card-view-btn" href="${escHtml(j.url)}" target="_blank" rel="noopener">View ↗</a>
        <button class="job-card-analyze-btn" onclick="analyzeJob(${i})">Analyze →</button>
      </div>
    </div>
  `;
  }).join('');
}

// Dismissals teach the system: the reason lands in
// private/jobs/learnings.md and the posting never resurfaces.
async function dismissJob(i) {
  const j = jobsData[i];
  const reason = prompt('Why skip it? One short reason — this builds your learnings file.\n(Leave blank to dismiss without one.)');
  if (reason === null) return; // cancelled
  try {
    await fetch('/api/dismiss', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: j.url, title: j.title, company: j.company, reason }),
    });
    jobsData.splice(i, 1);
    renderJobs(`Dismissed. ${reason ? 'Reason logged to learnings.md.' : ''} ${jobsData.length} posting(s) left.`);
  } catch {
    renderJobs('Dismiss failed — is the server running?');
  }
}

// Bridge: scraped posting → JD Analysis form, prefilled.
function analyzeJob(i) {
  const j = jobsData[i];
  document.getElementById('jd_company').value = j.company;
  document.getElementById('jd_role').value    = j.title;
  document.getElementById('jd_source').value  = j.url;
  document.getElementById('jd_posting').value = j.description || '';
  showSection('jd');
  window.scrollTo(0, 0);
}

// Bridge: scraped posting → tracker modal, prefilled.
function trackJob(i) {
  const j = jobsData[i];
  openAddModal();
  document.getElementById('entry_company').value = j.company;
  document.getElementById('entry_role').value    = j.title;
  document.getElementById('entry_channel').value = 'cold';
  document.getElementById('entry_status').value  = 'researching';
  document.getElementById('entry_notes').value   = `Found by scraper ${j.posted ? '(posted ' + j.posted + ')' : ''}. ${j.url}`;
}

// Watchlist editor — edits private/watchlist.md through the server.
async function loadWatchlistText() {
  try {
    const resp = await fetch('/api/watchlist');
    const data = await resp.json();
    document.getElementById('watchlist-text').value = data.text || '';
  } catch {}
}

function toggleWatchlist() {
  const editor = document.getElementById('watchlist-editor');
  const open = editor.style.display !== 'none';
  editor.style.display = open ? 'none' : 'block';
  document.getElementById('watchlist-toggle').textContent =
    open ? 'Edit watchlist ▸' : 'Edit watchlist ▾';
}

async function saveWatchlist() {
  const status = document.getElementById('watchlist-status');
  try {
    const resp = await fetch('/api/watchlist', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: document.getElementById('watchlist-text').value }),
    });
    const data = await resp.json();
    status.textContent = data.saved ? 'Saved ✓ — next scan uses it.' : (data.error || 'Save failed.');
  } catch {
    status.textContent = 'Save failed — is the server running?';
  }
  setTimeout(() => status.textContent = '', 3000);
}

// ─── JD Analysis ───────────────────────────────────────────

function runJDAnalysis() {
  const company  = document.getElementById('jd_company').value.trim();
  const role     = document.getElementById('jd_role').value.trim();
  const source   = document.getElementById('jd_source').value.trim();
  const posting  = document.getElementById('jd_posting').value.trim();

  if (!posting) {
    alert('Paste the job description first.');
    return;
  }

  const filename = `jd-${slugify(company || 'company')}-${slugify(role || 'role')}.md`;
  const md = `# Job Description Analysis

## The posting

- **Company:** ${company || '[Fill in]'}
- **Role title:** ${role || '[Fill in]'}
- **Source / link:** ${source || '[Fill in]'}
- **Date found:** ${today()}

## Decode the role

- **What they actually need:**
- **Seniority in practice:**
- **Red flags:**
- **Green flags:**

## Match assessment

- **Strong matches:**
- **Keyword gaps:**
- **Real gaps:**
- **Domain match:**

## Decision

- **Verdict:** apply / skip / stretch
- **Why, in one sentence:**
- **If applying — the angle:**

---

## Pasted job description

${posting}
`;

  // Save draft
  localStorage.setItem(JD_KEY, JSON.stringify({ company, role, source, posting }));

  downloadFile(filename, md);
}

function loadJDDraft() {
  try {
    const d = JSON.parse(localStorage.getItem(JD_KEY)) || {};
    if (d.company)  document.getElementById('jd_company').value  = d.company;
    if (d.role)     document.getElementById('jd_role').value     = d.role;
    if (d.source)   document.getElementById('jd_source').value   = d.source;
    if (d.posting)  document.getElementById('jd_posting').value  = d.posting;
  } catch {}
}

// ─── Tracker ───────────────────────────────────────────────

let trackerData = [];

function loadTracker() {
  try { trackerData = JSON.parse(localStorage.getItem(TRACKER_KEY)) || []; }
  catch { trackerData = []; }
}

function saveTracker() {
  localStorage.setItem(TRACKER_KEY, JSON.stringify(trackerData));
}

function renderTracker() {
  const tbody = document.getElementById('tracker-body');
  const empty = document.getElementById('tracker-empty');

  if (trackerData.length === 0) {
    tbody.innerHTML = '';
    empty.style.display = 'block';
    return;
  }

  empty.style.display = 'none';
  tbody.innerHTML = trackerData.map((r, i) => `
    <tr>
      <td><strong>${r.company || '—'}</strong></td>
      <td>${r.role || '—'}</td>
      <td>${r.channel || '—'}</td>
      <td>${r.applied || '—'}</td>
      <td><span class="status-pill">${r.status || 'researching'}</span></td>
      <td>${r.next || '—'}</td>
      <td>
        <button class="btn btn-ghost btn-sm" onclick="editEntry(${i})">Edit</button>
      </td>
    </tr>
  `).join('');
}

function openAddModal(editIndex = null) {
  const modal = document.getElementById('entry-modal');
  const entry = editIndex !== null ? trackerData[editIndex] : {};

  document.getElementById('modal-title').textContent = editIndex !== null ? 'Edit application' : 'Add application';
  document.getElementById('entry_company').value  = entry.company  || '';
  document.getElementById('entry_role').value     = entry.role     || '';
  document.getElementById('entry_channel').value  = entry.channel  || '';
  document.getElementById('entry_applied').value  = entry.applied  || today();
  document.getElementById('entry_status').value   = entry.status   || 'researching';
  document.getElementById('entry_next').value     = entry.next     || '';
  document.getElementById('entry_notes').value    = entry.notes    || '';
  document.getElementById('entry-modal').dataset.editIndex = editIndex ?? '';

  modal.classList.add('open');
}

function editEntry(i) { openAddModal(i); }

function closeModal() {
  document.getElementById('entry-modal').classList.remove('open');
}

function saveEntry() {
  const editIndex = document.getElementById('entry-modal').dataset.editIndex;
  const entry = {
    company: document.getElementById('entry_company').value.trim(),
    role:    document.getElementById('entry_role').value.trim(),
    channel: document.getElementById('entry_channel').value.trim(),
    applied: document.getElementById('entry_applied').value.trim(),
    status:  document.getElementById('entry_status').value.trim(),
    next:    document.getElementById('entry_next').value.trim(),
    notes:   document.getElementById('entry_notes').value.trim(),
  };

  if (editIndex !== '') {
    trackerData[parseInt(editIndex)] = entry;
  } else {
    trackerData.push(entry);
  }

  saveTracker();
  renderTracker();
  closeModal();
}

function exportTrackerMD() {
  if (trackerData.length === 0) { alert('No applications logged yet.'); return; }

  const rows = trackerData.map(r =>
    `| ${r.company} | ${r.role} | ${r.channel} | ${r.applied} | ${r.status} | ${r.next} |`
  ).join('\n');

  const md = `# Application Tracker

| Company | Role | Channel | Applied | Status | Next action |
|---|---|---|---|---|---|
${rows}

---
*Exported ${today()} from Job Hunter Toolkit*
`;
  downloadFile('tracker.md', md);
}

// ─── Utilities ─────────────────────────────────────────────

function downloadFile(filename, content) {
  const blob = new Blob([content], { type: 'text/markdown' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

function slugify(str) {
  return str.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

// ─── Init ───────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  loadNarrative();
  loadTracker();
  loadJDDraft();

  // Update home CTA if narrative exists
  if (hasNarrativeContent()) {
    const startBtn = document.getElementById('start-btn');
    if (startBtn) startBtn.textContent = 'View my narrative →';
  }

  renderWizard();
  renderTracker();
  showSection('home');

  // Close modal on backdrop click
  document.getElementById('entry-modal').addEventListener('click', e => {
    if (e.target === e.currentTarget) closeModal();
  });

  // Escape key closes modal
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModal();
  });
});
