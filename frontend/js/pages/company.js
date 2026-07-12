window.Pages = window.Pages || {};

Pages.CompanyDashboard = {
  components: { Stat: Components.Stat, Pill: Components.Pill },
  setup() {
    const { ref, onMounted } = Vue;
    const d = ref(null);
    async function load() { d.value = await API.get('/api/company/dashboard'); }
    async function close(id) {
      if (!confirm('Close this drive?')) return;
      try { const r = await API.post('/api/company/drives/'+id+'/close'); Store.toast(r.message); load(); }
      catch(e){ Store.toast(e.message,'err'); }
    }
    onMounted(load);
    return { d, close };
  },
  template: `
  <div class="container py-4" v-if="d">
    <div class="d-flex justify-content-between align-items-center mb-1">
      <div><div class="eyebrow">{{ d.company.industry || 'Company' }} · {{ d.company.location || '—' }}</div>
        <h2 class="mb-0">{{ d.company.company_name }}</h2></div>
      <router-link to="/company/drives/new" class="btn btn-amber">Create drive</router-link>
    </div>
    <div class="row g-3 my-2 mb-4">
      <div class="col-4"><Stat :n="d.total_drives" label="Drives" accent /></div>
      <div class="col-4"><Stat :n="d.total_applications" label="Applications" /></div>
      <div class="col-4"><Stat :n="d.shortlisted" label="Shortlisted" /></div>
    </div>
    <div class="card-flat">
      <div class="card-head">Your drives</div>
      <table class="table table-flat mb-0">
        <thead><tr><th>Drive</th><th>Role</th><th>Approval</th><th>Status</th><th>Applicants</th><th class="text-end">Action</th></tr></thead>
        <tbody>
          <tr v-for="dr in d.drives" :key="dr.id">
            <td>{{ dr.title }}</td><td>{{ dr.job_role }}</td>
            <td><Pill :value="dr.approval_status" /></td><td><Pill :value="dr.drive_status" /></td>
            <td>{{ dr.applicant_count }}</td>
            <td class="text-end">
              <router-link :to="'/company/drives/'+dr.id" class="btn btn-sm btn-ink me-1">Manage</router-link>
              <button v-if="dr.drive_status==='Open' && dr.approval_status==='Approved'"
                class="btn btn-sm btn-outline-secondary" @click="close(dr.id)">Close</button>
            </td>
          </tr>
          <tr v-if="!d.drives.length"><td colspan="6" class="empty">No drives yet — create your first one.</td></tr>
        </tbody>
      </table>
    </div>
  </div>`
};

Pages.CompanyCreateDrive = {
  setup() {
    const { reactive, ref } = Vue;
    const busy = ref(false);
    const f = reactive({ title:'', job_role:'', description:'', skills_required:'',
      package:'', eligibility_cgpa:'', eligibility_branch:'', eligibility_year:'',
      eligibility_criteria:'', application_deadline:'', drive_date:'' });
    async function submit() {
      busy.value = true;
      try { const r = await API.post('/api/company/drives', f); Store.toast(r.message); window.location.hash = '#/company'; }
      catch(e){ Store.toast(e.message,'err'); } finally { busy.value = false; }
    }
    return { f, busy, submit };
  },
  template: `
  <div class="container py-4" style="max-width:640px">
    <div class="eyebrow">New posting</div>
    <h2 class="mb-4">Create a placement drive</h2>
    <div class="card-flat"><div class="card-body">
      <div class="row g-2">
        <div class="col-6"><label class="form-label small">Drive name</label><input v-model="f.title" class="form-control form-control-sm" /></div>
        <div class="col-6"><label class="form-label small">Job title</label><input v-model="f.job_role" class="form-control form-control-sm" /></div>
        <div class="col-12"><label class="form-label small">Job description</label><textarea v-model="f.description" rows="3" class="form-control form-control-sm"></textarea></div>
        <div class="col-12"><label class="form-label small">Required skills</label><input v-model="f.skills_required" class="form-control form-control-sm" placeholder="Python, SQL" /></div>
        <div class="col-4"><label class="form-label small">Package (LPA)</label><input v-model="f.package" type="number" step="0.1" min="0" class="form-control form-control-sm" /></div>
        <div class="col-4"><label class="form-label small">Min CGPA</label><input v-model="f.eligibility_cgpa" type="number" step="0.1" min="0" max="10" class="form-control form-control-sm" /></div>
        <div class="col-4"><label class="form-label small">Min year</label><input v-model="f.eligibility_year" type="number" min="1" max="6" class="form-control form-control-sm" /></div>
        <div class="col-12"><label class="form-label small">Eligible branches <span class="text-muted">(comma-separated, blank = all)</span></label><input v-model="f.eligibility_branch" class="form-control form-control-sm" placeholder="CSE, ECE" /></div>
        <div class="col-6"><label class="form-label small">Application deadline</label><input v-model="f.application_deadline" type="date" class="form-control form-control-sm" /></div>
        <div class="col-6"><label class="form-label small">Drive date</label><input v-model="f.drive_date" type="date" class="form-control form-control-sm" /></div>
      </div>
      <button class="btn btn-amber mt-4" :disabled="busy" @click="submit">{{ busy?'Saving…':'Submit for approval' }}</button>
    </div></div>
  </div>`
};

Pages.CompanyViewDrive = {
  components: { Pill: Components.Pill },
  setup() {
    const { ref, onMounted } = Vue;
    const route = VueRouter.useRoute();
    const id = route.params.id;
    const data = ref(null);
    const iv = ref({});          // interview form per student
    async function load() { data.value = await API.get('/api/company/drives/'+id); }
    async function setStatus(a) {
      try { const r = await API.post('/api/company/applications/'+a.id+'/status', { status: a.application_status, remark: a.remark||'' });
        Store.toast(r.message); load(); } catch(e){ Store.toast(e.message,'err'); }
    }
    async function schedule(a) {
      const form = iv.value[a.id] || {};
      if (!form.scheduled_at) { Store.toast('Pick an interview date/time.','err'); return; }
      try {
        const r = await API.post('/api/company/drives/'+id+'/interviews',
          { student_id: a.student_id, scheduled_at: form.scheduled_at, mode: form.mode||'In-person', location: form.location||'' });
        Store.toast(r.message); iv.value[a.id] = {}; load();
      } catch(e){ Store.toast(e.message,'err'); }
    }
    onMounted(load);
    return { data, iv, setStatus, schedule, id };
  },
  template: `
  <div class="container py-4" v-if="data">
    <router-link to="/company" class="small">← Back to dashboard</router-link>
    <div class="d-flex justify-content-between align-items-baseline mt-2 mb-3">
      <div><div class="eyebrow">{{ data.drive.job_role }}</div><h2 class="mb-0">{{ data.drive.title }}</h2></div>
      <div><Pill :value="data.drive.approval_status" /> <Pill :value="data.drive.drive_status" /></div>
    </div>

    <div class="card-flat mb-4">
      <div class="card-head">Applicants ({{ data.applications.length }})</div>
      <table class="table table-flat mb-0">
        <thead><tr><th>Student</th><th>Dept</th><th>CGPA</th><th>Status</th><th>Resume</th><th style="width:120px">Remark</th><th class="text-end">Save</th></tr></thead>
        <tbody>
          <tr v-for="a in data.applications" :key="a.id">
            <td>{{ a.student_name }}</td><td>{{ a.student_department || '—' }}</td><td>{{ a.student_cgpa ?? '—' }}</td>
            <td>
              <select v-model="a.application_status" class="form-select form-select-sm" style="width:130px" :disabled="data.drive.approval_status!=='Approved'">
                <option>Applied</option><option>Shortlisted</option><option>Interview</option><option>Selected</option><option>Rejected</option><option>Placed</option>
              </select>
            </td>
            <td><a class="btn btn-sm btn-outline-secondary" :href="'/api/student/resume/'+a.student_id" target="_blank">View</a></td>
            <td><input v-model="a.remark" class="form-control form-control-sm" /></td>
            <td class="text-end"><button class="btn btn-sm btn-ink" @click="setStatus(a)">Save</button></td>
          </tr>
          <tr v-if="!data.applications.length"><td colspan="7" class="empty">No applicants yet</td></tr>
        </tbody>
      </table>
    </div>

    <div class="card-flat mb-4">
      <div class="card-head">Schedule interview</div>
      <table class="table table-flat mb-0">
        <thead><tr><th>Student</th><th>When</th><th>Mode</th><th>Location</th><th class="text-end">Schedule</th></tr></thead>
        <tbody>
          <tr v-for="a in data.applications" :key="'iv'+a.id">
            <td>{{ a.student_name }}</td>
            <td><input type="datetime-local" class="form-control form-control-sm" style="width:200px"
                  :value="(iv[a.id]||{}).scheduled_at" @input="iv[a.id]=Object.assign({},iv[a.id],{scheduled_at:$event.target.value})" /></td>
            <td><select class="form-select form-select-sm" style="width:120px"
                  :value="(iv[a.id]||{}).mode" @change="iv[a.id]=Object.assign({},iv[a.id],{mode:$event.target.value})">
                  <option>In-person</option><option>Online</option></select></td>
            <td><input class="form-control form-control-sm" placeholder="Room / link"
                  :value="(iv[a.id]||{}).location" @input="iv[a.id]=Object.assign({},iv[a.id],{location:$event.target.value})" /></td>
            <td class="text-end"><button class="btn btn-sm btn-amber" @click="schedule(a)">Schedule</button></td>
          </tr>
          <tr v-if="!data.applications.length"><td colspan="5" class="empty">No applicants to schedule</td></tr>
        </tbody>
      </table>
    </div>

    <div class="card-flat" v-if="data.interviews.length">
      <div class="card-head">Scheduled interviews</div>
      <table class="table table-flat mb-0">
        <thead><tr><th>Student</th><th>When</th><th>Mode</th><th>Location</th></tr></thead>
        <tbody>
          <tr v-for="i in data.interviews" :key="i.id">
            <td>{{ i.student_name }}</td><td>{{ (i.scheduled_at||'').replace('T',' ').slice(0,16) }}</td>
            <td>{{ i.mode }}</td><td>{{ i.location || '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>`
};
