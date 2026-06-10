var DisciplinasUI = {
    elements: {},

    init: function() {
        this.elements = {
            disciplinasGrid: document.getElementById('disciplinas-grid'),
            disciplinasEmpty: document.getElementById('disciplinas-empty'),
            btnSync: document.getElementById('btn-sync-disciplinas'),
        };
    },

    renderDisciplinas: function(disciplinas) {
        var grid = this.elements.disciplinasGrid;
        if (!grid) return;

        grid.innerHTML = '';

        if (!disciplinas || disciplinas.length === 0) {
            grid.innerHTML = '<div class="disciplinas-empty"><div class="empty-state-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg></div><h3>Nenhuma disciplina encontrada</h3><p>Clique no botao de sincronizar para buscar suas disciplinas no SUAP</p></div>';
            return;
        }

        var colors = ['#0A7F70', '#1565C0', '#6A1B9A', '#C62828', '#E65100', '#2E7D32', '#00838F', '#4527A0'];

        disciplinas.forEach(function(disc, index) {
            var color = colors[index % colors.length];
            var sigla = disc.sigla || (disc.descricao || '').substring(0, 3).toUpperCase();
            var situacaoClass = 'situacao-' + (disc.situacao || '').toLowerCase().replace(/\s/g, '-');

            var card = document.createElement('div');
            card.className = 'disciplina-card';
            card.innerHTML =
                '<div class="disciplina-header" style="background:' + color + '">' +
                    '<div class="disciplina-sigla">' + DisciplinasUI.escapeHtml(sigla) + '</div>' +
                    '<div class="disciplina-descricao-header">' + DisciplinasUI.escapeHtml(disc.descricao) + '</div>' +
                '</div>' +
                '<div class="disciplina-body">' +
                    (disc.professor ? '<div class="disciplina-info"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg><span>' + DisciplinasUI.escapeHtml(disc.professor) + '</span></div>' : '') +
                    (disc.situacao ? '<div class="disciplina-info"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg><span class="situacao-badge ' + situacaoClass + '">' + DisciplinasUI.escapeHtml(disc.situacao) + '</span></div>' : '') +
                    '<div class="disciplina-info"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg><span>' + DisciplinasUI.escapeHtml(disc.semestre) + '</span></div>' +
                '</div>';

            grid.appendChild(card);
        });
    },

    showLoading: function() {
        var grid = this.elements.disciplinasGrid;
        if (!grid) return;
        grid.innerHTML = '<div class="disciplinas-empty"><div class="disciplinas-loading"><div class="spinner"></div><p>Sincronizando com SUAP...</p></div></div>';
    },

    escapeHtml: function(text) {
        if (!text) return '';
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

window.DisciplinasUI = DisciplinasUI;
