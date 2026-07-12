const { createApp, h } = Vue;
const { createRouter, createWebHashHistory } = VueRouter;

const routes = [
  { path: '/', component: Pages.Landing },
  { path: '/login', component: Pages.Login, meta: { guestOnly: true } },
  { path: '/register', component: Pages.Register, meta: { guestOnly: true } },

  { path: '/admin', component: Pages.AdminDashboard, meta: { role: 'admin' } },
  { path: '/admin/companies', component: Pages.AdminCompanies, meta: { role: 'admin' } },
  { path: '/admin/students', component: Pages.AdminStudents, meta: { role: 'admin' } },
  { path: '/admin/drives', component: Pages.AdminDrives, meta: { role: 'admin' } },
  { path: '/admin/reports', component: Pages.AdminReports, meta: { role: 'admin' } },

  { path: '/company', component: Pages.CompanyDashboard, meta: { role: 'company' } },
  { path: '/company/drives/new', component: Pages.CompanyCreateDrive, meta: { role: 'company' } },
  { path: '/company/drives/:id', component: Pages.CompanyViewDrive, meta: { role: 'company' } },

  { path: '/student', component: Pages.StudentDashboard, meta: { role: 'student' } },
  { path: '/student/drives', component: Pages.StudentDrives, meta: { role: 'student' } },
  { path: '/student/applications', component: Pages.StudentApplications, meta: { role: 'student' } },
  { path: '/student/interviews', component: Pages.StudentInterviews, meta: { role: 'student' } },
  { path: '/student/profile', component: Pages.StudentProfile, meta: { role: 'student' } },

  { path: '/:pathMatch(.*)*', redirect: '/' },
];

const router = createRouter({ history: createWebHashHistory(), routes });

// Route guards: role gating + redirect authenticated users away from guest pages
router.beforeEach((to) => {
  const user = Store.state.user;
  if (to.meta.role) {
    if (!user) return '/login';
    if (user.role !== to.meta.role) return '/' + user.role;
  }
  if (to.meta.guestOnly && user) return '/' + user.role;
  return true;
});

const App = {
  components: { NavBar: Components.NavBar, Toasts: Components.Toasts },
  template: `<div><NavBar /><router-view /><Toasts /></div>`
};

const app = createApp(App);
app.component('router-link', VueRouter.RouterLink);
app.component('router-view', VueRouter.RouterView);
app.use(router);
app.mount('#app');