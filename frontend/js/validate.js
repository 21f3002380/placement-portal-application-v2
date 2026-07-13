// Lightweight client-side form validation helpers.
// Each validator returns an error string, or '' if the value is valid.
window.Validate = (function () {
  const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

  function required(value, label) {
    if (value === null || value === undefined || String(value).trim() === '') {
      return `${label} is required.`;
    }
    return '';
  }

  function email(value, label) {
    if (!value) return '';
    return EMAIL_RE.test(value.trim()) ? '' : `${label} must be a valid email address.`;
  }

  function minLength(value, len, label) {
    if (!value) return '';
    return value.length >= len ? '' : `${label} must be at least ${len} characters.`;
  }

  function numberInRange(value, lo, hi, label) {
    if (value === '' || value === null || value === undefined) return '';
    const n = Number(value);
    if (Number.isNaN(n)) return `${label} must be a number.`;
    if (lo !== null && n < lo) return `${label} must be at least ${lo}.`;
    if (hi !== null && n > hi) return `${label} must be at most ${hi}.`;
    return '';
  }

  function dateNotPast(value, label) {
    if (!value) return '';
    const d = new Date(value);
    const today = new Date(); today.setHours(0, 0, 0, 0);
    return d >= today ? '' : `${label} cannot be in the past.`;
  }

  // Runs a { field: [validators...] } spec against a { field: value } object.
  // Each validator is a function(value) -> errorString.
  // Returns { valid: bool, errors: { field: firstErrorOrEmptyString } }.
  function run(values, spec) {
    const errors = {};
    let valid = true;
    for (const field in spec) {
      for (const validator of spec[field]) {
        const err = validator(values[field]);
        if (err) { errors[field] = err; valid = false; break; }
      }
    }
    return { valid, errors };
  }

  return { required, email, minLength, numberInRange, dateNotPast, run };
})();