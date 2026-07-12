window.Pages = window.Pages || {};

Pages.Login = {
  setup() {
    const { ref } = Vue;
    const email = ref('');
    const password = ref('');
    const busy = ref(false);
    async function submit() {
      busy.value = true;
      try {
        const data = await API.post('/api/auth/login', { email: email.value, password: password.value });
        Store.setSession(data.token, data.user, data.profile);
        Store.toast('Welcome back.');
        window.location.hash = '#/' + data.user.role;
      } catch (e) {
        Store.toast(e.message, 'err');
      } finally { busy.value = false; }
    }
    return { email, password, busy, submit };
  },
  template: `
  <div class="auth-wrap">
    <div class="auth-side">
      <div class="eyebrow" style="color:#9fb0c2">Institute Placement Cell</div>
      <h1>Run campus recruitment without the spreadsheets.</h1>
      <p class="lede mt-3">Approvals, drives, applications, interviews and placement records — one console for admins, companies and students.</p>
    </div>
    <div class="auth-form">
      <div class="w-100" style="max-width:380px;margin:0 auto">
        <div class="eyebrow mb-1">Sign in</div>
        <h2 class="mb-4">Welcome back</h2>
        <div class="mb-3">
          <label class="form-label small">Email</label>
          <input v-model="email" type="email" class="form-control" @keyup.enter="submit" />
        </div>
        <div class="mb-4">
          <label class="form-label small">Password</label>
          <input v-model="password" type="password" class="form-control" @keyup.enter="submit" />
        </div>
        <button class="btn btn-amber w-100" :disabled="busy" @click="submit">
          {{ busy ? 'Signing in…' : 'Sign in' }}
        </button>
        <p class="small text-center mt-3 mb-0">New here? <router-link to="/register">Create an account</router-link></p>
        <p class="small text-center text-muted mt-2">Admin demo: admin@portal.com / Admin@123</p>
      </div>
    </div>
  </div>`
};

Pages.Register = {
  setup() {
    const { reactive, ref } = Vue;
    const role = ref('student');
    const busy = ref(false);
    const f = reactive({
      email: '', password: '', name: '', roll_number: '', department: '',
      year: '', cgpa: '', skills: '', experience: '',
      company_name: '', industry: '', location: '', hr_contact: '', website: '', description: ''
    });
    async function submit() {
      busy.value = true;
      try {
        const payload = Object.assign({ role: role.value }, f);
        const data = await API.post('/api/auth/register', payload);
        Store.toast(data.message);
        window.location.hash = '#/login';
      } catch (e) {
        Store.toast(e.message, 'err');
      } finally { busy.value = false; }
    }
    return { role, f, busy, submit };
  },
  template: `
  <div class="container" style="max-width:560px;padding:2.5rem 1rem">
    <div class="eyebrow mb-1">Create account</div>
    <h2 class="mb-4">Join the portal</h2>
    <div class="card-flat">
      <div class="card-body">
        <div class="btn-group w-100 mb-4">
          <button class="btn" :class="role==='student'?'btn-ink':'btn-outline-secondary'" @click="role='student'">Student</button>
          <button class="btn" :class="role==='company'?'btn-ink':'btn-outline-secondary'" @click="role='company'">Company</button>
        </div>

        <div class="row g-2">
          <div class="col-12"><label class="form-label small">Email</label>
            <input v-model="f.email" type="email" class="form-control form-control-sm" /></div>
          <div class="col-12"><label class="form-label small">Password</label>
            <input v-model="f.password" type="password" class="form-control form-control-sm" /></div>
        </div>

        <template v-if="role==='student'">
          <hr class="my-3" />
          <div class="row g-2">
            <div class="col-6"><label class="form-label small">Full name</label>
              <input v-model="f.name" class="form-control form-control-sm" /></div>
            <div class="col-6"><label class="form-label small">Roll number</label>
              <input v-model="f.roll_number" class="form-control form-control-sm" /></div>
            <div class="col-6"><label class="form-label small">Department</label>
              <input v-model="f.department" class="form-control form-control-sm" placeholder="e.g. CSE" /></div>
            <div class="col-3"><label class="form-label small">Year</label>
              <input v-model="f.year" type="number" min="1" max="6" class="form-control form-control-sm" /></div>
            <div class="col-3"><label class="form-label small">CGPA</label>
              <input v-model="f.cgpa" type="number" step="0.01" min="0" max="10" class="form-control form-control-sm" /></div>
            <div class="col-12"><label class="form-label small">Skills</label>
              <input v-model="f.skills" class="form-control form-control-sm" placeholder="Python, SQL, Vue" /></div>
          </div>
        </template>

        <template v-else>
          <hr class="my-3" />
          <div class="row g-2">
            <div class="col-12"><label class="form-label small">Company name</label>
              <input v-model="f.company_name" class="form-control form-control-sm" /></div>
            <div class="col-6"><label class="form-label small">Industry</label>
              <input v-model="f.industry" class="form-control form-control-sm" /></div>
            <div class="col-6"><label class="form-label small">Location</label>
              <input v-model="f.location" class="form-control form-control-sm" /></div>
            <div class="col-6"><label class="form-label small">HR contact</label>
              <input v-model="f.hr_contact" class="form-control form-control-sm" /></div>
            <div class="col-6"><label class="form-label small">Website</label>
              <input v-model="f.website" class="form-control form-control-sm" /></div>
            <div class="col-12"><label class="form-label small">Description</label>
              <textarea v-model="f.description" rows="2" class="form-control form-control-sm"></textarea></div>
          </div>
          <div class="alert alert-warning small mt-3 mb-0">Company accounts require admin approval before first login.</div>
        </template>

        <button class="btn btn-amber w-100 mt-4" :disabled="busy" @click="submit">
          {{ busy ? 'Submitting…' : 'Create account' }}
        </button>
        <p class="small text-center mt-3 mb-0">Already registered? <router-link to="/login">Sign in</router-link></p>
      </div>
    </div>
  </div>`
};