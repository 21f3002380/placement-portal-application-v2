window.Pages = window.Pages || {};

Pages.StudentDashboard = {
  components: { Pill: Components.Pill },
  setup() {
    const { ref, onMounted } = Vue;
    const d = ref(null);
    const exporting = ref(false);
    async function load() { d.value = await API.get('/api/student/dashboard'); }
    async function exportCsv() {
      exporting.value = true;
      try {
        const r = await API.post('/api/student/export');
        Store.toast(r.message);
        poll(r.task_id);
      } catch(e){ Store.toast(e.message,'err'); exporting.value = false; }
    }
    async function poll(taskId) {
      try {
        const s = await API.get('/api/student/export/'+taskId+'/status');
        if (s.state === 'SUCCESS' && s.result && s.result.filename) {
          Store.toast('Export ready — downloading.');
          window.open('/api/student/export/download/'+s.result.filename, '_blank');
          exporting.value = false;
        } else if (s.state === 'FAILURE') {
          Store.toast('Export failed.','err'); exporting.value = false;
        } else {
          setTimeout(() => poll(taskId), 1500);
        }
      } catch(e){ Store.toast(e.message,'err'); exporting.value = false; }
    }
    onMounted(load);
    return { d, exportCsv, exporting };
  },
  template: `
  <div class="container py-4" v-if="d">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div><div class="eyebrow">{{ d.student.department || 'Student' }} · CGPA {{ d.student.cgpa ?? '—' }}</div>
        <h2 class="mb-0">Hello, {{ d.student.name }}</h2></div>
      <div class="d-flex gap-2">
        <router-link to="/student/profile" class="btn btn-outline-secondary btn-sm">Edit profile</router-link>
        <button class="btn btn-ink btn-sm" :disabled="exporting" @click="exportCsv">{{ exporting?'Exporting…':'Export CSV' }}</button>
      </div>
    </div>

    <div class="card-flat mb-4">
      <div class="card-head">Approved companies</div>
      <div class="card-body">
        <div class="row g-2">
          <div class="col-md-4" v-for="c in d.companies" :key="c.id">
            <div class="border rounded p-2 d-flex justify-content-between align-items-center">
              <div><div class="fw-semibold">{{ c.company_name }}</div><div class="small text-muted">{{ c.location || '—' }}</div></div>
            </div>
          </div>
          <div v-if="!d.companies.length" class="empty">No approved companies yet</div>
        </div>
        <router-link to="/student/drives" class="btn btn-amber btn-sm mt-3">Browse open drives</router-link>
      </div>
    </div>

    <div class="card-flat">
      <div class="card-head">Your applications</div>
      <table class="table table-flat mb-0">
        <thead><tr><th>Drive</th><th>Company</th><th>Status</th><th>Applied</th></tr></thead>
        <tbody>
          <tr v-for="a in d.applications" :key="a.id">
            <td>{{ a.drive_title }}</td><td>{{ a.company_name }}</td>
            <td><Pill :value="a.application_status" /></td>
            <td class="small text-muted">{{ (a.applied_at||'').slice(0,10) }}</td>
          </tr>
          <tr v-if="!d.applications.length"><td colspan="4" class="empty">No applications yet</td></tr>
        </tbody>
      </table>
    </div>
  </div>`
};

Pages.StudentDrives = {
  components: { Pill: Components.Pill },
  setup() {
    const { ref, onMounted } = Vue;
    const list = ref([]); const q = ref('');
    async function load() { list.value = await API.get('/api/student/drives?q=' + encodeURIComponent(q.value)); }
    async function apply(d) {
      if (!confirm('Apply to ' + d.title + '?')) return;
      try { const r = await API.post('/api/student/drives/'+d.id+'/apply'); Store.toast(r.message); load(); }
      catch(e){ Store.toast(e.message,'err'); }
    }
    onMounted(load);
    return { list, q, load, apply };
  },
  template: `
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2 class="mb-0">Open drives</h2>
      <div class="d-flex gap-2">
        <input v-model="q" class="form-control form-control-sm" placeholder="Role, skill or company" @keyup.enter="load" style="width:240px" />
        <button class="btn btn-sm btn-ink" @click="load">Search</button>
      </div>
    </div>
    <div class="row g-3">
      <div class="col-md-6" v-for="d in list" :key="d.id">
        <div class="card-flat h-100"><div class="card-body">
          <div class="d-flex justify-content-between">
            <div><div class="eyebrow">{{ d.company_name }}</div><h4 class="mb-0">{{ d.title }}</h4>
              <div class="small text-muted">{{ d.job_role }} · {{ d.company_location || '—' }}</div></div>
            <div class="text-end"><div class="fw-semibold">{{ d.package ? d.package+' LPA' : '' }}</div></div>
          </div>
          <p class="small text-muted my-2">{{ d.description || 'No description provided.' }}</p>
          <div class="small mb-2">
            <span v-if="d.eligibility_cgpa" class="me-2">Min CGPA {{ d.eligibility_cgpa }}</span>
            <span v-if="d.eligibility_branch" class="me-2">Branches: {{ d.eligibility_branch }}</span>
            <span v-if="d.application_deadline">Deadline {{ d.application_deadline.slice(0,10) }}</span>
          </div>
          <button v-if="d.already_applied" class="btn btn-sm btn-outline-secondary" disabled>Applied</button>
          <button v-else-if="d.eligible" class="btn btn-sm btn-amber" @click="apply(d)">Apply</button>
          <span v-else class="small text-danger">{{ d.ineligible_reason }}</span>
        </div></div>
      </div>
      <div v-if="!list.length" class="empty">No open drives right now</div>
    </div>
  </div>`
};

Pages.StudentApplications = {
  components: { Pill: Components.Pill },
  setup() {
    const { ref, onMounted } = Vue;
    const list = ref([]);
    onMounted(async () => { list.value = await API.get('/api/student/applications'); });
    return { list };
  },
  template: `
  <div class="container py-4">
    <h2 class="mb-3">Application history</h2>
    <div class="card-flat">
      <table class="table table-flat mb-0">
        <thead><tr><th>Drive</th><th>Role</th><th>Company</th><th>Status</th><th>Remark</th><th>Applied</th></tr></thead>
        <tbody>
          <tr v-for="a in list" :key="a.id">
            <td>{{ a.drive_title }}</td><td>{{ a.job_role }}</td><td>{{ a.company_name }}</td>
            <td><Pill :value="a.application_status" /></td>
            <td class="small">{{ a.remark || '—' }}</td>
            <td class="small text-muted">{{ (a.applied_at||'').slice(0,10) }}</td>
          </tr>
          <tr v-if="!list.length"><td colspan="6" class="empty">No applications yet</td></tr>
        </tbody>
      </table>
    </div>
  </div>`
};

Pages.StudentInterviews = {
  setup() {
    const { ref, onMounted } = Vue;
    const list = ref([]);
    onMounted(async () => { list.value = await API.get('/api/student/interviews'); });
    return { list };
  },
  template: `
  <div class="container py-4">
    <h2 class="mb-3">Interview schedule</h2>
    <div class="card-flat">
      <table class="table table-flat mb-0">
        <thead><tr><th>Drive</th><th>When</th><th>Mode</th><th>Location</th><th>Feedback</th></tr></thead>
        <tbody>
          <tr v-for="i in list" :key="i.id">
            <td>{{ i.drive_title }}</td><td>{{ (i.scheduled_at||'').replace('T',' ').slice(0,16) }}</td>
            <td>{{ i.mode }}</td><td>{{ i.location || '—' }}</td><td class="small">{{ i.feedback || '—' }}</td>
          </tr>
          <tr v-if="!list.length"><td colspan="5" class="empty">No interviews scheduled</td></tr>
        </tbody>
      </table>
    </div>
  </div>`
};

Pages.StudentProfile = {
  setup() {
    const { reactive, ref, onMounted } = Vue;
    const f = reactive({ name:'', department:'', year:'', cgpa:'', skills:'', experience:'' });
    const resumeName = ref('');
    async function load() {
      const d = await API.get('/api/auth/me');
      Object.assign(f, {
        name: d.profile.name, department: d.profile.department, year: d.profile.year,
        cgpa: d.profile.cgpa, skills: d.profile.skills, experience: d.profile.experience
      });
      resumeName.value = d.profile.resume_filename || '';
    }
    async function save() {
      try { const r = await API.put('/api/student/profile', f); Store.toast(r.message); }
      catch(e){ Store.toast(e.message,'err'); }
    }
    async function uploadResume(ev) {
      const file = ev.target.files[0]; if (!file) return;
      const fd = new FormData(); fd.append('resume', file);
      try { const r = await API.postForm('/api/student/resume', fd); Store.toast(r.message); resumeName.value = r.resume_filename; }
      catch(e){ Store.toast(e.message,'err'); }
    }
    onMounted(load);
    return { f, resumeName, save, uploadResume };
  },
  template: `
  <div class="container py-4" style="max-width:560px">
    <h2 class="mb-4">Edit profile</h2>
    <div class="card-flat"><div class="card-body">
      <div class="row g-2">
        <div class="col-8"><label class="form-label small">Name</label><input v-model="f.name" class="form-control form-control-sm" /></div>
        <div class="col-4"><label class="form-label small">Year</label><input v-model="f.year" type="number" min="1" max="6" class="form-control form-control-sm" /></div>
        <div class="col-8"><label class="form-label small">Department</label><input v-model="f.department" class="form-control form-control-sm" /></div>
        <div class="col-4"><label class="form-label small">CGPA</label><input v-model="f.cgpa" type="number" step="0.01" min="0" max="10" class="form-control form-control-sm" /></div>
        <div class="col-12"><label class="form-label small">Skills</label><input v-model="f.skills" class="form-control form-control-sm" /></div>
        <div class="col-12"><label class="form-label small">Experience</label><textarea v-model="f.experience" rows="2" class="form-control form-control-sm"></textarea></div>
      </div>
      <button class="btn btn-amber mt-3" @click="save">Save profile</button>
      <hr class="my-3" />
      <label class="form-label small">Resume (PDF) <span class="text-muted" v-if="resumeName">— current: {{ resumeName }}</span></label>
      <input type="file" accept=".pdf" class="form-control form-control-sm" @change="uploadResume" />
    </div></div>
  </div>`
};
