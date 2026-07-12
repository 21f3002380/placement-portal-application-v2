window.Pages = window.Pages || {};

Pages.Landing = {
  setup() {
    const { ref, onMounted } = Vue;
    const stats = ref(null);
    const drives = ref([]);
    onMounted(async () => {
      try { stats.value = await API.get('/api/public/stats'); } catch(e) {}
      try { drives.value = await API.get('/api/public/drives'); } catch(e) {}
    });
    return { stats, drives };
  },
  template: `
  <div>
    <div style="background:var(--slate);color:#fff">
      <div class="container py-5">
        <div class="eyebrow" style="color:#9fb0c2">Institute Placement Cell</div>
        <h1 style="color:#fff;font-size:3rem;max-width:16ch">One console for the whole placement season.</h1>
        <p style="color:#b6c1cf;max-width:52ch" class="mt-3">Companies post drives, students apply, the cell approves and tracks every placement — all in one place, no spreadsheets.</p>
        <div class="mt-4 d-flex gap-2">
          <router-link to="/register" class="btn btn-amber">Get started</router-link>
          <router-link to="/login" class="btn btn-outline-light">Sign in</router-link>
        </div>
      </div>
    </div>
    <div class="container py-5" v-if="stats">
      <div class="row g-3 mb-5">
        <div class="col-6 col-md-3"><div class="stat accent"><div class="n">{{ stats.total_placements }}</div><div class="l">Placements</div></div></div>
        <div class="col-6 col-md-3"><div class="stat"><div class="n">{{ stats.total_companies }}</div><div class="l">Companies</div></div></div>
        <div class="col-6 col-md-3"><div class="stat"><div class="n">{{ stats.total_drives }}</div><div class="l">Drives</div></div></div>
        <div class="col-6 col-md-3"><div class="stat"><div class="n">{{ stats.total_students }}</div><div class="l">Students</div></div></div>
      </div>
      <div class="section-title"><div class="eyebrow">Live</div><h3 class="mb-0">Open drives</h3></div>
      <div class="row g-3">
        <div class="col-md-4" v-for="d in drives" :key="d.id">
          <div class="card-flat h-100"><div class="card-body">
            <div class="eyebrow">{{ d.company_name }}</div>
            <h5 class="mb-1">{{ d.title }}</h5>
            <div class="small text-muted">{{ d.job_role }} · {{ d.company_location || '—' }}</div>
            <div class="small mt-2" v-if="d.package">{{ d.package }} LPA</div>
          </div></div>
        </div>
        <div v-if="!drives.length" class="empty">No open drives right now</div>
      </div>
    </div>
  </div>`
};
