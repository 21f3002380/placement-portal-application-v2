window.Components = {};

// Status pill
Components.Pill = {
  props: ['value'],
  template: `<span class="pill" :class="(value||'').toLowerCase()">{{ value }}</span>`
};

// Stat card
Components.Stat = {
  props: ['n', 'label', 'accent'],
  template: `<div class="stat" :class="{accent}"><div class="n">{{ n }}</div><div class="l">{{ label }}</div></div>`
};

// Toast stack (reads Store)
Components.Toasts = {
  setup() { return { state: Store.state }; },
  template: `
    <div class="toast-stack">
      <div v-for="t in state.toasts" :key="t.id" class="toast-item" :class="t.kind==='err'?'err':'ok'">
        {{ t.message }}
      </div>
    </div>`
};

// Top navigation, role-aware
Components.NavBar = {
  setup() {
    const { computed } = Vue;
    const router = VueRouter.useRouter ? VueRouter.useRouter() : null;
    const user = computed(() => Store.state.user);
    function logout() {
      Store.clearSession();
      Store.toast('Signed out.');
      window.location.hash = '#/login';
    }
    return { user, logout };
  },
  template: `
    <nav class="brandbar py-2">
      <div class="container d-flex align-items-center">
        <router-link to="/" class="brand plain me-4">Placement<span class="dot">.</span>Portal</router-link>
        <template v-if="user">
          <div class="d-flex gap-3 me-auto small" v-if="user.role==='admin'">
            <router-link to="/admin">Dashboard</router-link>
            <router-link to="/admin/companies">Companies</router-link>
            <router-link to="/admin/students">Students</router-link>
            <router-link to="/admin/drives">Drives</router-link>
            <router-link to="/admin/reports">Reports</router-link>
          </div>
          <div class="d-flex gap-3 me-auto small" v-else-if="user.role==='company'">
            <router-link to="/company">Dashboard</router-link>
            <router-link to="/company/drives/new">New Drive</router-link>
          </div>
          <div class="d-flex gap-3 me-auto small" v-else-if="user.role==='student'">
            <router-link to="/student">Dashboard</router-link>
            <router-link to="/student/drives">Browse Drives</router-link>
            <router-link to="/student/applications">Applications</router-link>
            <router-link to="/student/interviews">Interviews</router-link>
          </div>
          <span class="small me-3" style="color:#9fb0c2"><i class="fa fa-user-circle"></i> {{ user.email }}</span>
          <button class="btn btn-sm btn-outline-light" @click="logout">Sign out</button>
        </template>
        <template v-else>
          <div class="ms-auto d-flex gap-3 small">
            <router-link to="/login">Login</router-link>
            <router-link to="/register">Register</router-link>
          </div>
        </template>
      </div>
    </nav>`
};

// Simple confirm helper
Components.confirmAction = (msg) => window.confirm(msg);
