(function() {
'use strict';

    var CONTRAST_KEY = 'acolhe-contrast';
    var FONT_SIZE_KEY = 'acolhe-font-size';

    // Accessibility Menu
function toggleAccessibilityMenu() {
    var menu = document.getElementById('accessibility-menu');
    if (!menu) return;
    
    // Toggle visibility
    menu.hidden = !menu.hidden;
}

function closeAccessibilityMenu() {
    var menu = document.getElementById('accessibility-menu');
    if (menu) {
        menu.hidden = true;
    }
}

// Alto Contraste
function getPreferredContrast() {
    return localStorage.getItem(CONTRAST_KEY) || 'normal';
}

function applyContrast(contrast) {
    if (contrast === 'high') {
        document.documentElement.setAttribute('data-contrast', 'high');
    } else {
        document.documentElement.removeAttribute('data-contrast');
    }
    localStorage.setItem(CONTRAST_KEY, contrast);
    updateContrastButton(contrast);
}

function toggleContrast() {
    var current = getPreferredContrast();
    var next = current === 'high' ? 'normal' : 'high';
    applyContrast(next);
}

function updateContrastButton(contrast) {
    var btn = document.getElementById('btn-alto-contraste');
    if (btn) {
        if (contrast === 'high') {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    }
}

// Font Size
function getPreferredFontSize() {
    return localStorage.getItem(FONT_SIZE_KEY) || 'normal';
}

function applyFontSize(size) {
    if (size === 'normal') {
        document.documentElement.removeAttribute('data-font-size');
    } else {
        document.documentElement.setAttribute('data-font-size', size);
    }
    localStorage.setItem(FONT_SIZE_KEY, size);
    updateFontSizeButtons(size);
}

function increaseFontSize() {
    var current = getPreferredFontSize();
    var next = current === 'normal' ? 'large' : current === 'large' ? 'xlarge' : 'xlarge';
    applyFontSize(next);
}

function decreaseFontSize() {
    var current = getPreferredFontSize();
    var next = current === 'xlarge' ? 'large' : current === 'large' ? 'normal' : 'normal';
    applyFontSize(next);
}

function updateFontSizeButtons(size) {
    var btnIncrease = document.getElementById('btn-aumentar-fonte');
    var btnDecrease = document.getElementById('btn-diminuir-fonte');
    
    if (btnIncrease) {
        btnIncrease.classList.toggle('active', size === 'xlarge');
    }
    if (btnDecrease) {
        btnDecrease.classList.toggle('active', size === 'normal');
    }
}

    function init() {
        var contrast = getPreferredContrast();
        applyContrast(contrast);

        var fontSize = getPreferredFontSize();
        applyFontSize(fontSize);

        var btnAccessibility = document.getElementById('btn-accessibility');
    if (btnAccessibility) {
        btnAccessibility.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleAccessibilityMenu();
        });
    }
    
    var btnContrast = document.getElementById('btn-alto-contraste');
    if (btnContrast) {
        btnContrast.addEventListener('click', function() {
            toggleContrast();
            closeAccessibilityMenu();
        });
    }
    
    var btnIncrease = document.getElementById('btn-aumentar-fonte');
    if (btnIncrease) {
        btnIncrease.addEventListener('click', function() {
            increaseFontSize();
            closeAccessibilityMenu();
        });
    }
    
    var btnDecrease = document.getElementById('btn-diminuir-fonte');
    if (btnDecrease) {
        btnDecrease.addEventListener('click', function() {
            decreaseFontSize();
            closeAccessibilityMenu();
        });
    }
    
    // Fechar menu ao clicar fora
    document.addEventListener('click', function(e) {
        var menu = document.getElementById('accessibility-menu');
        var btn = document.getElementById('btn-accessibility');
        if (menu && !menu.hidden && !menu.contains(e.target) && e.target !== btn) {
            closeAccessibilityMenu();
        }
    });
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

    window.AccessibilityToggle = {
    toggleContrast: toggleContrast,
    increaseFontSize: increaseFontSize,
    decreaseFontSize: decreaseFontSize,
    applyContrast: applyContrast,
    applyFontSize: applyFontSize,
};
})();