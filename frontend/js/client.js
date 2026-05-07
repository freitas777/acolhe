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
            console.error('[SuapClient] Erro SUAP:', error);
            alert('Falha na comunicação com o SUAP: ' + error.message);
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
