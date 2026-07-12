window.API = (function () {
  function token() { return localStorage.getItem('ppa_token') || ''; }

  async function request(method, url, body, isForm) {
    const headers = {};
    const t = token();
    if (t) headers['Authorization'] = 'Bearer ' + t;
    let payload;
    if (isForm) {
      payload = body; // FormData
    } else if (body !== undefined) {
      headers['Content-Type'] = 'application/json';
      payload = JSON.stringify(body);
    }
    const res = await fetch(url, { method, headers, body: payload });
    let data = null;
    try { data = await res.json(); } catch (e) { data = null; }
    if (!res.ok) {
      const msg = (data && data.error) ? data.error : ('Request failed (' + res.status + ')');
      throw new Error(msg);
    }
    return data;
  }

  return {
    get:  (u) => request('GET', u),
    post: (u, b) => request('POST', u, b || {}),
    put:  (u, b) => request('PUT', u, b || {}),
    postForm: (u, fd) => request('POST', u, fd, true),
  };
})();
