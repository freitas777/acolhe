var CLIENT_ID = '';
var REDIRECT_URI = '';
var SUAP_URL = '';
var SCOPE = '';
var SEMESTRE_VIGENTE = '';

(function() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/config', false);
  try {
    xhr.send();
    if (xhr.status === 200) {
      var cfg = JSON.parse(xhr.responseText);
      CLIENT_ID = cfg.suap_client_id || '';
      REDIRECT_URI = cfg.suap_redirect_uri || '';
      SUAP_URL = cfg.suap_base_url || '';
      SCOPE = cfg.suap_scope || '';
      SEMESTRE_VIGENTE = cfg.semestre_vigente || '';
    }
  } catch(e) {}
})();
