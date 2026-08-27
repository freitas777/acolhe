function acolheDecodeJWTPayload(token) {
 try {
  var parts = token.split('.');
  if (parts.length !== 3) return null;
  var b64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
  while (b64.length % 4) b64 += '=';
  return JSON.parse(decodeURIComponent(escape(atob(b64))));
 } catch(e) { return null; }
}

function acolheIsTokenExpired(token) {
 if (token.indexOf('.') === -1) return false;
 var payload = acolheDecodeJWTPayload(token);
 if (!payload || !payload.exp) return false;
 return (payload.exp * 1000) < Date.now();
}

function acolheIsAuthenticated() {
 var token = localStorage.getItem('acolhe_access_token');
 if (!token) return false;
 if (acolheIsTokenExpired(token)) {
  localStorage.removeItem('acolhe_access_token');
  return false;
 }
 return true;
}

function acolheLogout() {
 localStorage.removeItem('acolhe_access_token');
 var suap = window._suapClient;
  if (suap && suap.isAuthenticated && suap.isAuthenticated()) {
    suap.logout();
  } else {
    if (typeof Cookies !== 'undefined') {
      Cookies.remove('suapToken');
      Cookies.remove('suapTokenExpirationTime');
      Cookies.remove('suapScope');
    }
    window.location.replace('/');
  }
}

function acolheRequireAuth() {
  if (!acolheIsAuthenticated()) {
    window.location.replace('/');
    return false;
  }
  var token = acolheGetToken();
  var payload = acolheDecodeJWTPayload(token);
  if (payload && payload.senha_temporaria === true && window.location.pathname !== '/painel') {
    window.location.replace('/painel');
    return false;
  }
  return true;
}

function acolheGetToken() {
  return localStorage.getItem('acolhe_access_token') || '';
}

function acolheGetTipoPerfil() {
  var token = acolheGetToken();
  if (token) {
    var payload = acolheDecodeJWTPayload(token);
    if (payload && payload.tipo_perfil) return payload.tipo_perfil;
  }
  var stored = localStorage.getItem('acolhe_tipo_perfil');
  if (stored) return stored;
  return 'aluno';
}

function acolheGetRoleLabel() {
  var labels = {
    aluno: 'Aluno',
    professor: 'Professor',
    psicopedagogo: 'Psicopedagogo',
    admin: 'Administrador',
    servidor: 'Servidor'
  };
  return labels[acolheGetTipoPerfil()] || acolheGetTipoPerfil();
}

function acolheGetUserId() {
  var token = acolheGetToken();
  if (!token) return null;
  var payload = acolheDecodeJWTPayload(token);
  if (!payload || !payload.usuario_id) return null;
  return payload.usuario_id;
}

function acolheGetUserName() {
  var token = acolheGetToken();
  if (token) {
    var payload = acolheDecodeJWTPayload(token);
    if (payload && payload.nome) return payload.nome;
  }
  var stored = localStorage.getItem('acolhe_user_nome');
  if (stored) return stored;
  try {
    var user = JSON.parse(localStorage.getItem('acolhe_user') || '{}');
    if (user && user.nome) return user.nome;
  } catch(e) {}
  return 'Usuário';
}

// Limpa dados sensíveis antigos do localStorage (migração de segurança)
function acolheCleanupLegacyData() {
  localStorage.removeItem('acolhe_user_id');
  localStorage.removeItem('acolhe_senha_temporaria');
}

// Executa limpeza ao carregar
acolheCleanupLegacyData();

function acolheGetHomepage() {
    var perfil = acolheGetTipoPerfil();
    if (perfil === 'aluno' || perfil === 'professor') return '/disciplinas';
    if (perfil === 'psicopedagogo' || perfil === 'admin' || perfil === 'servidor') return '/painel';
    return '/disciplinas';
}

(function() {
    var logo = document.getElementById('topbar-logo');
    if (logo) logo.href = acolheGetHomepage();
})();

function acolheRequireRole(allowedRoles) {
 if (!acolheRequireAuth()) return false;
 var perfil = acolheGetTipoPerfil();
 if (allowedRoles.indexOf(perfil) === -1) {
  if (perfil === 'psicopedagogo' || perfil === 'admin' || perfil === 'servidor') {
   window.location.replace('/painel');
  } else {
   window.location.replace('/disciplinas');
  }
  return false;
 }
 return true;
}

function acolheFetch(url, options) {
 options = options || {};
 var token = acolheGetToken();
 if (token) {
  options.headers = options.headers || {};
  options.headers['Authorization'] = 'Bearer ' + token;
 }
 return fetch(url, options).then(function(r) {
  if (r.status === 401) {
   acolheLogout();
   return Promise.reject(new Error('Sessao expirada. Faca login novamente.'));
  }
  return r;
 });
}

var Token = function(value, expirationTimeInSeconds, scope) {
  var startTime = new Date().getTime();
  var finishTime = new Date(startTime + expirationTimeInSeconds * 1000);

  if (value) {
    Cookies.set('suapToken', value, { expires: finishTime});
  } else if (Cookies.get('suapToken')) {
    value = Cookies.get('suapToken');
  }
  if (expirationTimeInSeconds) {
    Cookies.set('suapTokenExpirationTime', finishTime, { expires: finishTime});
  } else if (Cookies.get('suapTokenExpirationTime')) {
    finishTime = new Date(Cookies.get('suapTokenExpirationTime'));
  }
  if (scope) {
    Cookies.set('suapScope', scope, { expires: finishTime});
  } else if (Cookies.get('suapScope')) {
    scope = Cookies.get('suapScope');
  }

    this.getValue = function() { return value; };
    this.getExpirationTime = function() { return finishTime; };
    this.getScope = function() { return scope; };
    this.isValid = function() {
        if (Cookies.get('suapToken') && value != null) { return true; }
        return false;
    };
    this.revoke = function() {
        value = null; startTime = null; finishTime = null;
        if (Cookies.get('suapToken')){ Cookies.remove('suapToken'); }
        if (Cookies.get('suapTokenExpirationTime')){ Cookies.remove('suapTokenExpirationTime'); }
        if (Cookies.get('suapScope')){ Cookies.remove('suapScope'); }
    };
};

var SuapClient = function(authHost, clientID, redirectURI, scope) {
    var authHost = authHost;
    var clientID = clientID;
    var redirectURI = redirectURI;
    var scope = scope;

    var resourceURL = authHost + '/api/rh/meus-dados/';
    var authorizationURL = authHost + '/o/authorize/';
    var logoutURL = authHost + '/o/revoke_token/';

    var responseType = 'token';
    var grantType = 'implicit';

    if (authHost.charAt(authHost.length - 1) == '/') {
        authHost = authHost.substr(0, authHost.length - 1);
    }

    var dataJSON;
    var token;

  var extractToken = function() {
    var match = document.location.hash.match(/access_token=([^&]+)/);
    if (match != null) { return match[1]; }
    return null;
  };

    var extractScope = function() {
        var match = document.location.hash.match(/scope=(.*)/);
        if (match != null) { return match[1].split('+').join(' '); }
        return null;
    };

    var extractDuration = function() {
        var match = document.location.hash.match(/expires_in=(\d+)/);
        if (match != null) { return Number(!!match && match[1]); }
        return 0;
    };

    this.init = function() {
        token = new Token(extractToken(), extractDuration(), extractScope());
        dataJSON = {};
    };

    this.getToken = function() { return token; };
    this.getDataJSON = function() { return dataJSON; };
    this.getRedirectURI = function() { return redirectURI; };
    this.isAuthenticated = function() { return token.isValid(); };

    this.getLoginURL = function() {
        var loginUrl = authorizationURL +
            "?response_type=" + responseType +
            "&client_id=" + clientID +
            "&scope=" + scope +
            "&redirect_uri=" + redirectURI;
        return loginUrl;
    };

    this.getResource = function(scope, callback) {
        fetch(resourceURL, {
            headers: {
                "Authorization": "Bearer " + token.getValue(),
                "Accept": "application/json"
            }
        })
        .then(function(response) {
            if (!response.ok) throw new Error('HTTP ' + response.status);
            return response.json();
        })
        .then(function(data) {
            callback(data);
        })
    .catch(function(error) {
      alert('Falha na comunicacao com o SUAP: ' + error.message);
    });
    };

    this.login = function() {
        window.location = this.getLoginURL();
    };

    this.logout = function() {
        fetch(logoutURL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: 'token=' + encodeURIComponent(token.getValue()) + '&client_id=' + encodeURIComponent(clientID)
        })
        .then(function() {
            token.revoke();
            window.location = redirectURI;
        })
        .catch(function() {
            alert('Falha na comunicação com o SUAP');
        });
    };
};
