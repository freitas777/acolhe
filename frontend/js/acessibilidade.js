(function() {
  'use strict';

  var STORAGE_KEY = 'acolhe-acessibilidade';

  var defaults = {
    regua: false,
    foco: false,
    dislexia: false,
    daltonismo: 'nenhum'
  };

  var state = loadState();
  var fab = null;
  var panel = null;
  var reguaEl = null;
  var focoSpotlight = null;

  function loadState() {
    try {
      var stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        var parsed = JSON.parse(stored);
        return {
          regua: !!parsed.regua,
          foco: !!parsed.foco,
          dislexia: !!parsed.dislexia,
          daltonismo: parsed.daltonismo || 'nenhum'
        };
      }
    } catch (e) {}
    return { regua: false, foco: false, dislexia: false, daltonismo: 'nenhum' };
  }

  function saveState() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) {}
  }

  function createSVGFilters() {
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '0');
    svg.setAttribute('height', '0');
    svg.style.position = 'absolute';
    svg.innerHTML = '<defs>' +
      '<filter id="acessibilidade-filtro-protanopia">' +
      '<feColorMatrix type="matrix" values="0.567,0.433,0,0,0 0.558,0.442,0,0,0 0,0.242,0.758,0,0 0,0,0,1,0"/>' +
      '</filter>' +
      '<filter id="acessibilidade-filtro-deuteranopia">' +
      '<feColorMatrix type="matrix" values="0.625,0.375,0,0,0 0.7,0.3,0,0,0 0,0.3,0.7,0,0 0,0,0,1,0"/>' +
      '</filter>' +
      '<filter id="acessibilidade-filtro-tritanopia">' +
      '<feColorMatrix type="matrix" values="0.95,0.05,0,0,0 0,0.433,0.567,0,0 0,0.475,0.525,0,0 0,0,0,1,0"/>' +
      '</filter>' +
      '</defs>';
    document.body.appendChild(svg);
  }

  function createFAB() {
    fab = document.createElement('button');
    fab.className = 'acessibilidade-fab';
    fab.setAttribute('aria-label', 'Opcoes de acessibilidade');
    fab.setAttribute('aria-expanded', 'false');
    fab.setAttribute('title', 'Acessibilidade');
    fab.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
      '<circle cx="12" cy="12" r="10"/>' +
      '<path d="M12 16v-4"/>' +
      '<path d="M12 8h.01"/>' +
      '</svg>';
    fab.addEventListener('click', togglePanel);
    document.body.appendChild(fab);
  }

  function createPanel() {
    panel = document.createElement('div');
    panel.className = 'acessibilidade-panel';
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-label', 'Opcoes de acessibilidade');

    panel.innerHTML =
      '<div class="acessibilidade-panel-header">' +
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
      '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>' +
      '</svg>' +
      '<h3>Acessibilidade</h3>' +
      '</div>' +

      '<div class="acessibilidade-section">' +
      '<div class="acessibilidade-section-title">Leitura e Foco</div>' +

      '<div class="acessibilidade-toggle" data-feature="regua">' +
      '<div class="acessibilidade-toggle-info">' +
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
      '<rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>' +
      '<line x1="3" y1="9" x2="21" y2="9"/>' +
      '<line x1="3" y1="15" x2="21" y2="15"/>' +
      '</svg>' +
      '<div>' +
      '<div class="acessibilidade-toggle-label">Regua de Leitura</div>' +
      '<div class="acessibilidade-toggle-desc">Destaca a linha do cursor</div>' +
      '</div>' +
      '</div>' +
      '<label class="acessibilidade-switch">' +
      '<input type="checkbox" id="acess-toggle-regua" ' + (state.regua ? 'checked' : '') + '>' +
      '<span class="acessibilidade-switch-slider"></span>' +
      '</label>' +
      '</div>' +

      '<div class="acessibilidade-toggle" data-feature="foco">' +
      '<div class="acessibilidade-toggle-info">' +
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
      '<circle cx="12" cy="12" r="10"/>' +
      '<circle cx="12" cy="12" r="3"/>' +
      '</svg>' +
      '<div>' +
      '<div class="acessibilidade-toggle-label">Modo de Foco</div>' +
      '<div class="acessibilidade-toggle-desc">Escurece tudo exceto o bloco atual</div>' +
      '</div>' +
      '</div>' +
      '<label class="acessibilidade-switch">' +
      '<input type="checkbox" id="acess-toggle-foco" ' + (state.foco ? 'checked' : '') + '>' +
      '<span class="acessibilidade-switch-slider"></span>' +
      '</label>' +
      '</div>' +

      '</div>' +

      '<div class="acessibilidade-section">' +
      '<div class="acessibilidade-section-title">Fonte</div>' +

      '<div class="acessibilidade-toggle" data-feature="dislexia">' +
      '<div class="acessibilidade-toggle-info">' +
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
      '<polyline points="4 7 4 4 20 4 20 7"/>' +
      '<line x1="9" y1="20" x2="15" y2="20"/>' +
      '<line x1="12" y1="4" x2="12" y2="20"/>' +
      '</svg>' +
      '<div>' +
      '<div class="acessibilidade-toggle-label">Fonte para Dislexia</div>' +
      '<div class="acessibilidade-toggle-desc">Fonte OpenDyslexic</div>' +
      '</div>' +
      '</div>' +
      '<label class="acessibilidade-switch">' +
      '<input type="checkbox" id="acess-toggle-dislexia" ' + (state.dislexia ? 'checked' : '') + '>' +
      '<span class="acessibilidade-switch-slider"></span>' +
      '</label>' +
      '</div>' +

      '</div>' +

      '<div class="acessibilidade-section">' +
      '<div class="acessibilidade-section-title">Cores</div>' +

      '<div class="acessibilidade-select-wrapper">' +
      '<label for="acess-select-daltonismo">Filtro para Daltonismo</label>' +
      '<select id="acess-select-daltonismo" class="acessibilidade-select">' +
      '<option value="nenhum"' + (state.daltonismo === 'nenhum' ? ' selected' : '') + '>Nenhum</option>' +
      '<option value="protanopia"' + (state.daltonismo === 'protanopia' ? ' selected' : '') + '>Protanopia (vermelho)</option>' +
      '<option value="deuteranopia"' + (state.daltonismo === 'deuteranopia' ? ' selected' : '') + '>Deuteranopia (verde)</option>' +
      '<option value="tritanopia"' + (state.daltonismo === 'tritanopia' ? ' selected' : '') + '>Tritanopia (azul)</option>' +
      '</select>' +
      '</div>' +

      '</div>';

    document.body.appendChild(panel);

    panel.querySelector('#acess-toggle-regua').addEventListener('change', function() {
      state.regua = this.checked;
      applyRegua();
      saveState();
    });

    panel.querySelector('#acess-toggle-foco').addEventListener('change', function() {
      state.foco = this.checked;
      applyFoco();
      saveState();
    });

    panel.querySelector('#acess-toggle-dislexia').addEventListener('change', function() {
      state.dislexia = this.checked;
      applyDislexia();
      saveState();
    });

    panel.querySelector('#acess-select-daltonismo').addEventListener('change', function() {
      state.daltonismo = this.value;
      applyDaltonismo();
      saveState();
    });

    var toggles = panel.querySelectorAll('.acessibilidade-toggle');
    for (var i = 0; i < toggles.length; i++) {
      (function(toggle) {
    toggle.addEventListener('click', function(e) {
      if (e.target.closest('label, input')) return;
      var input = toggle.querySelector('input[type="checkbox"]');
      if (input) {
        input.checked = !input.checked;
        input.dispatchEvent(new Event('change'));
      }
    });
      })(toggles[i]);
    }
  }

  function createRegua() {
    reguaEl = document.createElement('div');
    reguaEl.className = 'acessibilidade-regua';
    document.body.appendChild(reguaEl);

    document.addEventListener('mousemove', function(e) {
      if (!state.regua || !reguaEl) return;
      var y = e.clientY - 20;
      if (y < 0) y = 0;
      reguaEl.style.top = y + 'px';
    });
  }

  function createFocoSpotlight() {
    focoSpotlight = document.createElement('div');
    focoSpotlight.className = 'acessibilidade-foco-spotlight';
    document.body.appendChild(focoSpotlight);

    document.addEventListener('mousemove', function(e) {
      if (!state.foco || !focoSpotlight) return;

      var el = document.elementFromPoint(e.clientX, e.clientY);
      if (!el || el === focoSpotlight || el === fab || el === panel || panel.contains(el)) {
        focoSpotlight.style.display = 'none';
        return;
      }

      var blockEl = el;
      while (blockEl && blockEl !== document.body) {
        var rect = blockEl.getBoundingClientRect();
        if (rect.height > 20 && rect.width > 100) break;
        blockEl = blockEl.parentElement;
      }
      if (!blockEl || blockEl === document.body) blockEl = el;

      var rect = blockEl.getBoundingClientRect();
      var padding = 8;

      focoSpotlight.style.display = 'block';
      focoSpotlight.style.top = (rect.top - padding) + 'px';
      focoSpotlight.style.left = (rect.left - padding) + 'px';
      focoSpotlight.style.width = (rect.width + padding * 2) + 'px';
      focoSpotlight.style.height = (rect.height + padding * 2) + 'px';
    });
  }

  function togglePanel() {
    var isOpen = panel.classList.contains('open');
    if (isOpen) {
      panel.classList.remove('open');
      fab.setAttribute('aria-expanded', 'false');
    } else {
      panel.classList.add('open');
      fab.setAttribute('aria-expanded', 'true');
    }
  }

  function closePanel() {
    if (panel && panel.classList.contains('open')) {
      panel.classList.remove('open');
      fab.setAttribute('aria-expanded', 'false');
    }
  }

  function applyRegua() {
    if (state.regua) {
      document.body.classList.add('acessibilidade-regua-ativa');
    } else {
      document.body.classList.remove('acessibilidade-regua-ativa');
    }
  }

  function applyFoco() {
    if (state.foco) {
      document.body.classList.add('acessibilidade-foco-ativo');
    } else {
      document.body.classList.remove('acessibilidade-foco-ativo');
      if (focoSpotlight) focoSpotlight.style.display = 'none';
    }
  }

  function applyDislexia() {
    if (state.dislexia) {
      document.body.classList.add('acessibilidade-dislexia');
    } else {
      document.body.classList.remove('acessibilidade-dislexia');
    }
  }

  function applyDaltonismo() {
    document.body.classList.remove(
      'acessibilidade-daltonismo-protanopia',
      'acessibilidade-daltonismo-deuteranopia',
      'acessibilidade-daltonismo-tritanopia'
    );
    if (state.daltonismo && state.daltonismo !== 'nenhum') {
      document.body.classList.add('acessibilidade-daltonismo-' + state.daltonismo);
    }
  }

  function applyAll() {
    applyRegua();
    applyFoco();
    applyDislexia();
    applyDaltonismo();
  }

  function init() {
    createSVGFilters();
    createFAB();
    createPanel();
    createRegua();
    createFocoSpotlight();
    applyAll();

    document.addEventListener('click', function(e) {
      if (!panel || !fab) return;
      if (!panel.classList.contains('open')) return;
      if (panel.contains(e.target) || fab.contains(e.target)) return;
      closePanel();
    });

    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') closePanel();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
