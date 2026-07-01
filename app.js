// Job Hunter Assistant — app.js
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

*Generated by Job Hunter Assistant — https://github.com/[your-handle]/job-hunter-assistant*
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

// Human-friendly names for aggregator sources surfaced in `posting.also_on`.
// Falls back to capitalizing the raw value for anything not in the map.
function prettySource(raw) {
  if (!raw) return '';
  const key = String(raw).trim().toLowerCase().replace(/[\s_-]/g, '');
  const map = {
    remoteok: 'RemoteOK',
    weworkremotely: 'WeWorkRemotely',
    remotive: 'Remotive',
  };
  if (map[key]) return map[key];
  const s = String(raw).trim();
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// "Also listed on" row: secondary, muted links to the same role on
// less-canonical aggregator boards. De-dupes by display name. Returns ''
// when `also_on` is missing/empty so no row renders.
function alsoOnRow(alsoOn) {
  if (!Array.isArray(alsoOn) || alsoOn.length === 0) return '';
  const seen = new Set();
  const links = [];
  for (const entry of alsoOn) {
    if (!entry || !entry.source || !entry.url) continue;
    const name = prettySource(entry.source);
    if (!name || seen.has(name)) continue;
    seen.add(name);
    links.push(`<a href="${escHtml(entry.url)}" target="_blank" rel="noopener">${escHtml(name)}</a>`);
  }
  if (!links.length) return '';
  return `<div class="job-card-also-on">Also on: ${links.join(' · ')}</div>`;
}

// Short watchlist-tier chip: signals *why this surfaced* (a watchlist
// preference), distinct from keyword chips. Maps the tier text to a short
// label by substring; returns '' (no chip) when nothing matches or absent.
function tierChip(tier) {
  if (!tier || typeof tier !== 'string') return '';
  const t = tier.toLowerCase();
  let label = '';
  if (t.includes('gaming')) label = 'Gaming';
  else if (t.includes('entertainment')) label = 'Entertainment';
  else if (t.includes('design-systems') || t.includes('design systems')) label = 'Design systems';
  else if (t.includes('agenc') || t.includes('consultanc')) label = 'Agency';
  else if (t.includes('seattle') || t.includes('bellevue') || t.includes('redmond')) label = 'Seattle area';
  if (!label) return '';
  return `<span class="job-card-chip job-card-tier-chip" title="${escHtml('Watchlist tier: ' + tier)}">${escHtml(label)}</span>`;
}

// "Applied" status stamp: a calm, scannable signal that this posting is already
// in the tracker. Defensive — returns '' when posting.applied is absent.
function appliedBadge(applied) {
  if (!applied || typeof applied !== 'object') return '';
  const date = applied.date ? String(applied.date).trim() : '';
  let status = applied.status ? String(applied.status).trim() : '';
  // Don't echo a status that just repeats the badge word ("Applied · Applied").
  if (status.toLowerCase() === 'applied') status = '';
  const tipParts = ['Applied', date, status].filter(Boolean);
  const tip = tipParts.length > 1
    ? tipParts[0] + ' ' + tipParts.slice(1).join(' · ')
    : 'Applied';
  const closed = applied.section === 'closed' ? ' job-card-applied-badge-closed' : '';
  return `<span class="job-card-chip job-card-applied-badge${closed}" title="${escHtml(tip)}">✓ Applied</span>`;
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
    const tierChipHtml = tierChip(j.tier);
    const alsoOnHtml = alsoOnRow(j.also_on);
    const appliedBadgeHtml = appliedBadge(j.applied);

    return `
    <div class="job-card">
      <div class="job-card-body">
        <div class="job-card-identity">
          <div class="job-card-title-row">
            <div class="job-card-title">${escHtml(j.title)}</div>
            ${appliedBadgeHtml}
          </div>
          <div class="job-card-company">
            <span class="job-card-co-name">${escHtml(j.company)}</span>
          </div>
          <div class="job-card-location-row">
            ${locWithSalary ? `<span class="job-card-location">${locWithSalary}</span>` : ''}
            <span class="job-card-provenance">${j.posted ? j.posted : 'Undated'} · ${escHtml(j.source)}</span>
          </div>
          ${alsoOnHtml}
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
        ${(chips.length || tierChipHtml) ? `<div class="job-card-chips">${tierChipHtml}${chips.map(c => `<span class="job-card-chip">${escHtml(c)}</span>`).join('')}</div>` : ''}
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

// Bridge: scraped posting → tracker.
// Phase 1 is read-only — the tracker mirrors private/tracker.md and has no
// in-app write path yet. Surface a copy-paste-ready row instead.
function trackJob(i) {
  const j = jobsData[i];
  const row = `| ${j.company} | ${j.title} | cold | ${today()} | researching | — | Found by scraper${j.posted ? ' (posted ' + j.posted + ')' : ''}. ${j.url} |`;
  alert('Editing the tracker in-app lands in Phase 2.\n\nFor now, paste this row under "## Active" in private/tracker.md:\n\n' + row);
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

// Phase 1: read-only view of private/tracker.md, served by serve.py at
// GET /api/tracker → { active: [...], closed: [...], patterns: "<md>" }.
// Editing is Phase 2 — for now we render the file faithfully. Cell values
// may contain markdown (bold, links, emoji); mdInline() renders them safely.
let trackerData = { active: [], closed: [], patterns: '' };

async function loadTracker() {
  const status = document.getElementById('tracker-status');
  if (status) status.textContent = '';
  try {
    const resp = await fetch('/api/tracker');
    if (!resp.ok) throw new Error(resp.status);
    const data = await resp.json();
    trackerData = {
      active:   Array.isArray(data.active) ? data.active : [],
      closed:   Array.isArray(data.closed) ? data.closed : [],
      patterns: typeof data.patterns === 'string' ? data.patterns : '',
    };
  } catch {
    trackerData = { active: [], closed: [], patterns: '' };
    if (status) status.textContent = 'Could not load the tracker — is the server running? (start serve.py)';
  }
  renderTracker();
}

// Minimal, safe inline markdown → HTML for table cells. Escapes first, then
// re-introduces a small set of inline patterns. Emoji/dashes pass through as
// plain text. Not a full parser — Phase 1 just needs readability.
function mdInline(str) {
  if (str == null) return '';
  let s = escHtml(String(str));
  // links [text](url) — only http(s)/mailto to avoid javascript: injection
  s = s.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+|mailto:[^\s)]+)\)/g,
    (m, text, url) => `<a href="${url}" target="_blank" rel="noopener">${text}</a>`);
  // bold **x**
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  // italics *x* / _x_
  s = s.replace(/(^|[^*])\*([^*]+)\*(?!\*)/g, '$1<em>$2</em>');
  s = s.replace(/(^|[^_])_([^_]+)_(?!_)/g, '$1<em>$2</em>');
  // inline code `x`
  s = s.replace(/`([^`]+)`/g, '<code>$1</code>');
  return s;
}

// Render a markdown block readably without a heavy parser: paragraphs,
// "- " bullets, and inline formatting via mdInline(). Good enough for Phase 1.
function mdBlock(str) {
  if (!str || !str.trim()) return '<p class="text-muted">No patterns recorded yet.</p>';
  const lines = String(str).replace(/\r\n/g, '\n').split('\n');
  let html = '';
  let inList = false;
  for (const raw of lines) {
    const line = raw.trim();
    const bullet = line.match(/^[-*]\s+(.*)$/);
    const heading = line.match(/^(#{1,6})\s+(.*)$/);
    if (bullet) {
      if (!inList) { html += '<ul>'; inList = true; }
      html += `<li>${mdInline(bullet[1])}</li>`;
      continue;
    }
    if (inList) { html += '</ul>'; inList = false; }
    if (heading) {
      const level = Math.min(heading[1].length + 2, 6);
      html += `<h${level}>${mdInline(heading[2])}</h${level}>`;
    } else if (line) {
      html += `<p>${mdInline(line)}</p>`;
    }
  }
  if (inList) html += '</ul>';
  return html;
}

function renderTracker() {
  const content = document.getElementById('tracker-content');
  const empty   = document.getElementById('tracker-empty');
  const active  = trackerData.active || [];
  const closed  = trackerData.closed || [];
  const patterns = trackerData.patterns || '';

  const isEmpty = active.length === 0 && closed.length === 0 && !patterns.trim();
  if (empty)   empty.style.display   = isEmpty ? 'block' : 'none';
  if (content) content.style.display = isEmpty ? 'none'  : 'block';
  if (isEmpty) return;

  const activeList = document.getElementById('tracker-active-body');
  activeList.innerHTML = active.length
    ? active.map(r => trackerCard(r, false)).join('')
    : `<p class="tracker-card-empty text-muted">No active applications.</p>`;

  const closedList = document.getElementById('tracker-closed-body');
  closedList.innerHTML = closed.length
    ? closed.map(r => trackerCard(r, true)).join('')
    : `<p class="tracker-card-empty text-muted">Nothing closed out yet.</p>`;

  document.getElementById('tracker-patterns').innerHTML = mdBlock(patterns);
}

// One application = one card. Active and Closed share the same shape; the
// short fields differ (Status pill vs Outcome) and the full-width block at the
// bottom is Notes (Active) or "What I learned" (Closed). Cell values may carry
// markdown, so mdInline() renders them. The card reflows responsively via CSS —
// the meta line wraps and collapses to a stack on narrow widths.
function trackerCard(r, isClosed) {
  const company = mdInline(r.company) || '—';
  const role    = mdInline(r.role);
  const channel = mdInline(r.channel);
  const applied = mdInline(r.applied);

  // Meta items: small labeled facts that wrap freely.
  const meta = [];
  if (channel) meta.push(`<span class="tracker-meta-item"><span class="tracker-meta-label">Channel</span>${channel}</span>`);
  if (applied) meta.push(`<span class="tracker-meta-item"><span class="tracker-meta-label">Applied</span>${applied}</span>`);

  if (isClosed) {
    const outcome = mdInline(r.outcome);
    if (outcome) meta.push(`<span class="tracker-meta-item"><span class="tracker-meta-label">Outcome</span><span class="status-pill">${outcome}</span></span>`);
  } else {
    const status = mdInline(r.status);
    if (status) meta.push(`<span class="tracker-meta-item"><span class="tracker-meta-label">Status</span><span class="status-pill">${status}</span></span>`);
  }

  // Next action (Active only) gets its own line.
  const next = isClosed ? '' : mdInline(r.next);
  const nextRow = next
    ? `<div class="tracker-card-line"><span class="tracker-line-label">Next</span><span class="tracker-line-val">${next}</span></div>`
    : '';

  // Full-width block: Notes (Active) or What I learned (Closed) — the
  // "pseudo-row within the row" that spans the card.
  const blockLabel = isClosed ? 'What I learned' : 'Notes';
  const blockVal   = isClosed ? mdInline(r.learned) : mdInline(r.notes);
  const block = blockVal
    ? `<div class="tracker-card-block"><span class="tracker-line-label">${blockLabel}</span><div class="tracker-block-val">${blockVal}</div></div>`
    : '';

  return `
    <article class="tracker-card">
      <div class="tracker-card-head">
        <span class="tracker-card-company">${company}</span>
        ${role ? `<span class="tracker-card-role">${role}</span>` : ''}
      </div>
      ${meta.length ? `<div class="tracker-card-meta">${meta.join('')}</div>` : ''}
      ${nextRow}
      ${block}
    </article>`;
}

// Phase 2 will add in-app editing (POST /api/tracker with a surgical block
// write to the Active table). The add/edit modal and its handlers were
// removed in Phase 1 to keep the tracker a faithful read-only view of the MD.

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
  loadJDDraft();

  // Update home CTA if narrative exists
  if (hasNarrativeContent()) {
    const startBtn = document.getElementById('start-btn');
    if (startBtn) startBtn.textContent = 'View my narrative →';
  }

  renderWizard();
  loadTracker(); // async fetch of /api/tracker, then renders
  showSection('home');
});
