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

  // Downloads for JWT-protected files (resumes, CSV exports) can't use a
  // plain <a href> or window.open() — browsers don't attach custom headers
  // to those navigations, so the Authorization header never reaches the
  // server and the route 401s. Instead: fetch the file WITH the header,
  // then trigger a save via a temporary blob link.
  async function download(url, filename) {
    const headers = {};
    const t = token();
    if (t) headers['Authorization'] = 'Bearer ' + t;
    const res = await fetch(url, { headers });
    if (!res.ok) {
      let msg = 'Download failed (' + res.status + ')';
      try { const data = await res.json(); if (data.error) msg = data.error; } catch (e) {}
      throw new Error(msg);
    }
    const blob = await res.blob();
    const blobUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = filename || 'download';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(blobUrl);
  }

  async function openInNewTab(url) {
    const headers = {};
    const t = token();
    if (t) headers['Authorization'] = 'Bearer ' + t;
    const res = await fetch(url, { headers });
    if (!res.ok) {
      let msg = 'Could not open file (' + res.status + ')';
      try { const data = await res.json(); if (data.error) msg = data.error; } catch (e) {}
      throw new Error(msg);
    }
    const blob = await res.blob();
    const blobUrl = URL.createObjectURL(blob);
    window.open(blobUrl, '_blank');
    // Revoke later so the new tab has time to load it.
    setTimeout(() => URL.revokeObjectURL(blobUrl), 60000);
  }

  return {
    get:  (u) => request('GET', u),
    post: (u, b) => request('POST', u, b || {}),
    put:  (u, b) => request('PUT', u, b || {}),
    postForm: (u, fd) => request('POST', u, fd, true),
    download,
    openInNewTab,
  };
})();
