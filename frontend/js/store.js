window.Store = (function () {
  const { reactive } = Vue;

  const state = reactive({
    user: JSON.parse(localStorage.getItem('ppa_user') || 'null'),
    profile: JSON.parse(localStorage.getItem('ppa_profile') || 'null'),
    toasts: [],
  });

  let toastId = 0;

  function setSession(token, user, profile) {
    localStorage.setItem('ppa_token', token);
    localStorage.setItem('ppa_user', JSON.stringify(user));
    localStorage.setItem('ppa_profile', JSON.stringify(profile || null));
    state.user = user;
    state.profile = profile || null;
  }

  function clearSession() {
    localStorage.removeItem('ppa_token');
    localStorage.removeItem('ppa_user');
    localStorage.removeItem('ppa_profile');
    state.user = null;
    state.profile = null;
  }

  function toast(message, kind) {
    const id = ++toastId;
    state.toasts.push({ id, message, kind: kind || 'ok' });
    setTimeout(() => {
      const i = state.toasts.findIndex(t => t.id === id);
      if (i > -1) state.toasts.splice(i, 1);
    }, 3500);
  }

  return { state, setSession, clearSession, toast };
})();
