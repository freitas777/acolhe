(function() {
'use strict';

var NotificacaoService = {
    _pollInterval: null,
    _dropdownOpen: false,
    _eventsBound: false,

    init: function() {
        if (!acolheIsAuthenticated()) return;
        this._renderBell();
        if (!this._eventsBound) {
            this._bindEvents();
            this._eventsBound = true;
        }
        this.fetchCount();
        this.startPolling();
    },

    _renderBell: function() {
        var containers = document.querySelectorAll('.notificacao-bell-container');
        for (var i = 0; i < containers.length; i++) {
            if (containers[i].querySelector('.notificacao-bell')) continue;
            containers[i].innerHTML =
                '<button class="notificacao-bell" title="Notificacoes" aria-label="Notificacoes">' +
                    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
                        '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>' +
                        '<path d="M13.73 21a2 2 0 0 1-3.46 0"/>' +
                    '</svg>' +
                    '<span class="notificacao-badge" hidden>0</span>' +
                '</button>' +
                '<div class="notificacao-dropdown" hidden>' +
                    '<div class="notificacao-dropdown-header">' +
                        '<span>Notificacoes</span>' +
                        '<button class="notificacao-marcar-todas" title="Marcar todas como lidas">Marcar todas como lidas</button>' +
                    '</div>' +
                    '<div class="notificacao-dropdown-list"></div>' +
                    '<a href="/notificacoes" class="notificacao-dropdown-footer">Ver todas</a>' +
                '</div>';
        }
    },

    _bindEvents: function() {
        var self = this;
        document.addEventListener('click', function(e) {
            var bell = e.target.closest('.notificacao-bell');
            if (bell) {
                e.preventDefault();
                e.stopPropagation();
                self.toggleDropdown();
                return;
            }
            var markAllBtn = e.target.closest('.notificacao-marcar-todas');
            if (markAllBtn) {
                e.preventDefault();
                e.stopPropagation();
                self.markAllRead();
                return;
            }
 var item = e.target.closest('.notificacao-item');
 if (item) {
 e.preventDefault();
 e.stopPropagation();
 var id = parseInt(item.getAttribute('data-id'), 10);
 if (!isNaN(id)) {
 self.markAsRead(id);
 }
 return;
 }
 var deleteBtn = e.target.closest('.notificacao-item-delete');
 if (deleteBtn) {
 e.preventDefault();
 e.stopPropagation();
 var id = parseInt(deleteBtn.getAttribute('data-id'), 10);
 if (!isNaN(id)) {
 self.deleteNotificacao(id);
 }
 return;
 }
            if (self._dropdownOpen) {
                var dropdown = e.target.closest('.notificacao-dropdown');
                if (!dropdown) {
                    self.closeDropdown();
                }
            }
        });
    },

    toggleDropdown: function() {
        if (this._dropdownOpen) {
            this.closeDropdown();
        } else {
            this.openDropdown();
        }
    },

    openDropdown: function() {
        var dropdowns = document.querySelectorAll('.notificacao-dropdown');
        for (var i = 0; i < dropdowns.length; i++) {
            dropdowns[i].hidden = false;
        }
        this._dropdownOpen = true;
        this.fetchRecent();
    },

    closeDropdown: function() {
        var dropdowns = document.querySelectorAll('.notificacao-dropdown');
        for (var i = 0; i < dropdowns.length; i++) {
            dropdowns[i].hidden = true;
        }
        this._dropdownOpen = false;
    },

    fetchCount: function() {
        var self = this;
        acolheFetch('/notificacoes/count')
            .then(function(r) { return r.json(); })
            .then(function(data) {
                self.updateBadge(data.nao_lidas || 0);
            })
            .catch(function() {});
    },

    fetchRecent: function() {
        var self = this;
        acolheFetch('/notificacoes/?limit=5')
            .then(function(r) { return r.json(); })
            .then(function(data) {
                self.renderDropdownList(data);
            })
            .catch(function() {});
    },

    updateBadge: function(count) {
        var badges = document.querySelectorAll('.notificacao-badge');
        for (var i = 0; i < badges.length; i++) {
            if (count > 0) {
                badges[i].textContent = count > 99 ? '99+' : count;
                badges[i].hidden = false;
            } else {
                badges[i].textContent = '0';
                badges[i].hidden = true;
            }
        }
    },

    renderDropdownList: function(notificacoes) {
        var lists = document.querySelectorAll('.notificacao-dropdown-list');
        var self = this;
        for (var i = 0; i < lists.length; i++) {
            var listEl = lists[i];
            if (!notificacoes || notificacoes.length === 0) {
                listEl.innerHTML = '<div class="notificacao-empty">Nenhuma notificacao</div>';
                continue;
            }
            var html = '';
            for (var j = 0; j < notificacoes.length; j++) {
                var n = notificacoes[j];
                var lidaClass = n.lida ? 'notificacao-item-lida' : 'notificacao-item-nao-lida';
                var alunoTag = n.aluno_nome ? ' <span class="notificacao-aluno-tag">' + self._escapeHtml(n.aluno_nome) + '</span>' : '';
 html += '<div class="notificacao-item ' + lidaClass + '" data-id="' + n.id + '">' +
 '<div class="notificacao-item-content">' +
 '<div class="notificacao-item-titulo">' + self._escapeHtml(n.titulo) + alunoTag + '</div>' +
 (n.mensagem ? '<div class="notificacao-item-mensagem">' + self._escapeHtml(n.mensagem) + '</div>' : '') +
 '<div class="notificacao-item-data">' + self._formatTime(n.criada_em) + '</div>' +
 '</div>' +
 '<button class="notificacao-item-delete" data-id="' + n.id + '" title="Remover">' +
 '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>' +
 '</button>' +
 '</div>';
            }
            listEl.innerHTML = html;
        }
    },

    markAsRead: function(id) {
        var self = this;
        acolheFetch('/notificacoes/' + id + '/ler', { method: 'PUT' })
            .then(function() {
                self.fetchCount();
                if (self._dropdownOpen) self.fetchRecent();
            })
            .catch(function() {});
    },

 markAllRead: function() {
 var self = this;
 acolheFetch('/notificacoes/ler-todas', { method: 'PUT' })
 .then(function() {
 self.updateBadge(0);
 if (self._dropdownOpen) self.fetchRecent();
 })
 .catch(function() {});
 },

 deleteNotificacao: function(id) {
 var self = this;
 acolheFetch('/notificacoes/' + id, { method: 'DELETE' })
 .then(function() {
 self.fetchCount();
 if (self._dropdownOpen) self.fetchRecent();
 })
 .catch(function() {});
 },

    startPolling: function() {
        var self = this;
        if (this._pollInterval) return;
        this._pollInterval = setInterval(function() {
            self.fetchCount();
        }, 30000);
    },

    stopPolling: function() {
        if (this._pollInterval) {
            clearInterval(this._pollInterval);
            this._pollInterval = null;
        }
    },

    _escapeHtml: function(str) {
        if (!str) return '';
        var div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    _formatTime: function(isoStr) {
        if (!isoStr) return '';
        try {
            var d = new Date(isoStr);
            if (isNaN(d.getTime())) return '';
            var now = new Date();
            var diffMs = now - d;
            var diffMin = Math.floor(diffMs / 60000);
            if (diffMin < 1) return 'agora';
            if (diffMin < 60) return diffMin + ' min';
            var diffH = Math.floor(diffMin / 60);
            if (diffH < 24) return diffH + 'h';
            var diffD = Math.floor(diffH / 24);
            if (diffD < 7) return diffD + 'd';
            return d.toLocaleDateString('pt-BR');
        } catch(e) { return ''; }
    }
};

window.NotificacaoService = NotificacaoService;
})();
