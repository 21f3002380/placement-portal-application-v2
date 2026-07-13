window.Pages = window.Pages || {};

Pages.AdminDashboard = {
  components: { Stat: Components.Stat, Pill: Components.Pill },
  setup() {
    const { ref, onMounted } = Vue;
    const d = ref(null);
    async function load() { d.value = await API.get('/api/admin/dashboard'); }
    async function act(url, ok) { try { const r = await API.post(url); Store.toast(r.message||ok); load(); } catch(e){ Store.toast(e.message,'err'); } }
    onMounted(load);
    return { d, act };
  },
  template: `
  <div class="container py-4" v-if="d">
    <div class="section-title"><div><div class="eyebrow">Institute</div><h2 class="mb-0">Admin overview</h2></div></div>
    <div class="row g-3 mb-4">
      <div class="col-6 col-md-3"><Stat :n="d.total_students" label="Students" accent /></div>
      <div class="col-6 col-md-3"><Stat :n="d.total_companies" label="Companies" /></div>
      <div class="col-6 col-md-3"><Stat :n="d.total_drives" label="Drives" /></div>
      <div class="col-6 col-md-3"><Stat :n="d.total_applications" label="Applications" /></div>
    </div>

    <div class="card-flat mb-4">
      <div class="card-head">Companies awaiting approval</div>
      <table class="table table-flat mb-0">
        <thead><tr><th>Company</th><th>Email</th><th>Industry</th><th class="text-end">Action</th></tr></thead>
        <tbody>
          <tr v-for="c in d.pending_companies" :key="c.id">
            <td>{{ c.company_name }}</td><td>{{ c.email }}</td><td>{{ c.industry || '—' }}</td>
            <td class="text-end">
              <button class="btn btn-sm btn-amber me-1" @click="act('/api/admin/companies/'+c.id+'/approve')">Approve</button>
              <button class="btn btn-sm btn-outline-danger" @click="act('/api/admin/companies/'+c.id+'/reject')">Reject</button>
            </td>
          </tr>
          <tr v-if="!d.pending_companies.length"><td colspan="4" class="empty">No pending companies</td></tr>
        </tbody>
      </table>
    </div>

    <div class="card-flat mb-4">
      <div class="card-head">Drives awaiting approval</div>
      <table class="table table-flat mb-0">
        <thead><tr><th>Drive</th><th>Company</th><th>Role</th><th class="text-end">Action</th></tr></thead>
        <tbody>
          <tr v-for="dr in d.pending_drives" :key="dr.id">
            <td>{{ dr.title }}</td><td>{{ dr.company_name }}</td><td>{{ dr.job_role }}</td>
            <td class="text-end">
              <button class="btn btn-sm btn-amber me-1" @click="act('/api/admin/drives/'+dr.id+'/approve')">Approve</button>
              <button class="btn btn-sm btn-outline-danger" @click="act('/api/admin/drives/'+dr.id+'/reject')">Reject</button>
            </td>
          </tr>
          <tr v-if="!d.pending_drives.length"><td colspan="4" class="empty">No pending drives</td></tr>
        </tbody>
      </table>
    </div>

    <div class="card-flat">
      <div class="card-head">Recent applications</div>
      <table class="table table-flat mb-0">
        <thead><tr><th>Student</th><th>Drive</th><th>Company</th><th>Status</th><th>Applied</th></tr></thead>
        <tbody>
          <tr v-for="a in d.recent_applications" :key="a.id">
            <td>{{ a.student_name }}</td><td>{{ a.drive_title }}</td><td>{{ a.company_name }}</td>
            <td><Pill :value="a.application_status" /></td>
            <td class="small text-muted">{{ (a.applied_at||'').slice(0,10) }}</td>
          </tr>
          <tr v-if="!d.recent_applications.length"><td colspan="5" class="empty">No applications yet</td></tr>
        </tbody>
      </table>
    </div>
  </div>`
};

Pages.AdminCompanies = {
  components: { Pill: Components.Pill },
  setup() {
    const { ref, onMounted } = Vue;
    const list = ref([]); const q = ref('');
    async function load() { list.value = await API.get('/api/admin/companies?q=' + encodeURIComponent(q.value)); }
    async function act(url) { try { const r = await API.post(url); Store.toast(r.message); load(); } catch(e){ Store.toast(e.message,'err'); } }
    onMounted(load);
    return { list, q, load, act };
  },
  template: `
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2 class="mb-0">Companies</h2>
      <div class="d-flex gap-2">
        <input v-model="q" class="form-control form-control-sm" placeholder="Name or industry" @keyup.enter="load" style="width:220px" />
        <button class="btn btn-sm btn-ink" @click="load">Search</button>
      </div>
    </div>
    <div class="card-flat">
      <table class="table table-flat mb-0">
        <thead><tr><th>Company</th><th>Email</th><th>Industry</th><th>Status</th><th class="text-end">Actions</th></tr></thead>
        <tbody>
          <tr v-for="c in list" :key="c.id">
            <td>{{ c.company_name }}</td><td>{{ c.email }}</td><td>{{ c.industry || '—' }}</td>
            <td>
              <Pill v-if="c.is_blacklisted" value="Blacklisted" />
              <Pill v-else-if="c.is_approved" value="Approved" />
              <Pill v-else value="Pending" />
            </td>
            <td class="text-end">
              <button v-if="!c.is_approved && !c.is_blacklisted" class="btn btn-sm btn-amber me-1" @click="act('/api/admin/companies/'+c.id+'/approve')">Approve</button>
              <button v-if="!c.is_blacklisted" class="btn btn-sm btn-outline-danger" @click="act('/api/admin/companies/'+c.id+'/blacklist')">Blacklist</button>
              <button v-else class="btn btn-sm btn-outline-secondary" @click="act('/api/admin/companies/'+c.id+'/unblacklist')">Restore</button>
            </td>
          </tr>
          <tr v-if="!list.length"><td colspan="5" class="empty">No companies</td></tr>
        </tbody>
      </table>
    </div>
  </div>`
};

Pages.AdminStudents = {
  components: { Pill: Components.Pill },
  setup() {
    const { ref, onMounted } = Vue;
    const list = ref([]); const q = ref('');
    async function load() { list.value = await API.get('/api/admin/students?q=' + encodeURIComponent(q.value)); }
    async function act(url) { try { const r = await API.post(url); Store.toast(r.message); load(); } catch(e){ Store.toast(e.message,'err'); } }
    async function viewResume(studentId) {
      try { await API.openInNewTab('/api/student/resume/'+studentId); }
      catch(e){ Store.toast(e.message, 'err'); }
    }
    onMounted(load);
    return { list, q, load, act, viewResume};
  },
  template: `
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2 class="mb-0">Students</h2>
      <div class="d-flex gap-2">
        <input v-model="q" class="form-control form-control-sm" placeholder="Name, roll or email" @keyup.enter="load" style="width:220px" />
        <button class="btn btn-sm btn-ink" @click="load">Search</button>
      </div>
    </div>
    <div class="card-flat">
      <table class="table table-flat mb-0">
        <thead><tr><th>Name</th><th>Email</th><th>Roll</th><th>Dept</th><th>CGPA</th><th>Status</th><th class="text-end">Actions</th></tr></thead>
        <tbody>
          <tr v-for="s in list" :key="s.id">
            <td>{{ s.name }}</td><td class="small">{{ s.email }}</td><td>{{ s.roll_number }}</td><td>{{ s.department || '—' }}</td><td>{{ s.cgpa ?? '—' }}</td>
            <td><Pill v-if="s.is_blacklisted" value="Blacklisted" /><Pill v-else value="Active" /></td>
            <td class="text-end">
              <a class="btn btn-sm btn-outline-secondary me-1" v-if="s.resume_filename" @click="viewResume(s.id)">Resume</a>
              <button v-if="!s.is_blacklisted" class="btn btn-sm btn-outline-danger" @click="act('/api/admin/students/'+s.id+'/blacklist')">Blacklist</button>
              <button v-else class="btn btn-sm btn-outline-secondary" @click="act('/api/admin/students/'+s.id+'/unblacklist')">Restore</button>
            </td>
          </tr>
          <tr v-if="!list.length"><td colspan="7" class="empty">No students</td></tr>
        </tbody>
      </table>
    </div>
  </div>`
};

Pages.AdminDrives = {
  components: { Pill: Components.Pill },
  setup() {
    const { ref, onMounted } = Vue;
    const list = ref([]); const filter = ref('all');
    async function load() { list.value = await API.get('/api/admin/drives?status=' + filter.value); }
    async function act(url) { try { const r = await API.post(url); Store.toast(r.message); load(); } catch(e){ Store.toast(e.message,'err'); } }
    function setF(v){ filter.value = v; load(); }
    onMounted(load);
    return { list, filter, act, setF };
  },
  template: `
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2 class="mb-0">Placement drives</h2>
      <div class="btn-group btn-group-sm">
        <button v-for="s in ['All','Pending','Approved','Rejected']" :key="s"
          class="btn" :class="filter===s?'btn-ink':'btn-outline-secondary'" @click="setF(s)">{{ s }}</button>
      </div>
    </div>
    <div class="card-flat">
      <table class="table table-flat mb-0">
        <thead><tr><th>Drive</th><th>Company</th><th>Role</th><th>Approval</th><th>Status</th><th class="text-end">Action</th></tr></thead>
        <tbody>
          <tr v-for="d in list" :key="d.id">
            <td>{{ d.title }}</td><td>{{ d.company_name }}</td><td>{{ d.job_role }}</td>
            <td><Pill :value="d.approval_status" /></td><td><Pill :value="d.drive_status" /></td>
            <td class="text-end">
              <button v-if="d.approval_status==='Pending'" class="btn btn-sm btn-amber me-1" @click="act('/api/admin/drives/'+d.id+'/approve')">Approve</button>
              <button v-if="d.approval_status!=='Rejected'" class="btn btn-sm btn-outline-danger" @click="act('/api/admin/drives/'+d.id+'/reject')">Reject</button>
            </td>
          </tr>
          <tr v-if="!list.length"><td colspan="6" class="empty">No drives</td></tr>
        </tbody>
      </table>
    </div>
  </div>`
};

Pages.AdminReports = {
  setup() {
    const { ref, onMounted, nextTick } = Vue;
    const s = ref(null);
    const charts = {};
    function destroyAll() { Object.values(charts).forEach(c => c && c.destroy()); }

    const STATUS_COLORS = {
      Applied: '#d7e3f2', Shortlisted: '#fbeecd', Interview: '#d5eef2',
      Selected: '#d9ecdf', Placed: '#2f7d55', Rejected: '#f4d9d6',
    };

    async function load() {
      s.value = await API.get('/api/admin/stats');
      await nextTick();
      destroyAll();

      const companyCtx = document.getElementById('companyChart');
      if (companyCtx) {
        charts.company = new Chart(companyCtx, {
          type: 'bar',
          data: {
            labels: s.value.company_stats.map(c => c.company),
            datasets: [
              { label: 'Applications', data: s.value.company_stats.map(c => c.applications), backgroundColor: '#33475f' },
              { label: 'Selected', data: s.value.company_stats.map(c => c.selected), backgroundColor: '#d98a2b' },
            ]
          },
          options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
        });
      }

      const funnelCtx = document.getElementById('funnelChart');
      if (funnelCtx) {
        const labels = Object.keys(s.value.status_distribution);
        charts.funnel = new Chart(funnelCtx, {
          type: 'doughnut',
          data: {
            labels,
            datasets: [{
              data: labels.map(l => s.value.status_distribution[l]),
              backgroundColor: labels.map(l => STATUS_COLORS[l] || '#c9c2b4'),
            }]
          },
          options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
        });
      }

      const trendCtx = document.getElementById('trendChart');
      if (trendCtx) {
        charts.trend = new Chart(trendCtx, {
          type: 'line',
          data: {
            labels: s.value.monthly_placements.map(m => m.month),
            datasets: [{
              label: 'Placements', data: s.value.monthly_placements.map(m => m.count),
              borderColor: '#d98a2b', backgroundColor: 'rgba(217,138,43,0.15)',
              fill: true, tension: 0.3,
            }]
          },
          options: { responsive: true, plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } }
        });
      }

      const skillsCtx = document.getElementById('skillsChart');
      if (skillsCtx) {
        charts.skills = new Chart(skillsCtx, {
          type: 'bar',
          data: {
            labels: s.value.skills_demand.map(d => d.skill),
            datasets: [{ label: 'Drives requiring this skill', data: s.value.skills_demand.map(d => d.count), backgroundColor: '#33475f' }]
          },
          options: { indexAxis: 'y', responsive: true, plugins: { legend: { display: false } },
                    scales: { x: { beginAtZero: true, ticks: { precision: 0 } } } }
        });
      }
    }
    onMounted(load);
    return { s };
  },
  template: `
  <div class="container py-4" v-if="s">
    <div class="eyebrow">Analytics</div>
    <h2 class="mb-4">Placement reports</h2>
    <div class="row g-3 mb-4">
      <div class="col-6 col-md-3"><div class="stat accent"><div class="n">{{ s.placed_students }}</div><div class="l">Placed students</div></div></div>
      <div class="col-6 col-md-3"><div class="stat"><div class="n">{{ s.total_students }}</div><div class="l">Total students</div></div></div>
      <div class="col-6 col-md-3"><div class="stat"><div class="n">{{ s.drives_open }}</div><div class="l">Open drives</div></div></div>
      <div class="col-6 col-md-3"><div class="stat"><div class="n">{{ s.drives_closed }}</div><div class="l">Closed drives</div></div></div>
    </div>

    <div class="row g-3 mb-3">
      <div class="col-md-6">
        <div class="card-flat h-100">
          <div class="card-head">Application funnel</div>
          <div class="card-body"><canvas id="funnelChart" height="180"></canvas></div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card-flat h-100">
          <div class="card-head">Placement trend (last 6 months)</div>
          <div class="card-body"><canvas id="trendChart" height="180"></canvas></div>
        </div>
      </div>
    </div>

    <div class="row g-3 mb-3">
      <div class="col-md-6">
        <div class="card-flat h-100">
          <div class="card-head">Job demand by skills</div>
          <div class="card-body">
            <canvas id="skillsChart" height="200"></canvas>
            <p v-if="!s.skills_demand.length" class="empty mb-0">No skills data yet</p>
          </div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card-flat h-100">
          <div class="card-head">Applications vs selections by company</div>
          <div class="card-body">
            <canvas id="companyChart" height="200"></canvas>
            <p v-if="!s.company_stats.length" class="empty mb-0">No company data yet</p>
          </div>
        </div>
      </div>
    </div>
  </div>`
};