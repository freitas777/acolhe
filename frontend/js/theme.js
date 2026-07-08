(function() {
'use strict';

var THEME_KEY = 'acolhe-theme';
var CONTRAST_KEY = 'acolhe-contrast';
var FONT_SIZE_KEY = 'acolhe-font-size';

function getPreferredTheme() {
    var stored = localStorage.getItem(THEME_KEY);
    if (stored) return stored;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
    updateButtonIcon(theme);
}

function updateButtonIcon(theme) {
    var btn = document.getElementById('btn-dark-mode');
    if (!btn) return;
    
    if (theme === 'dark') {
        btn.innerHTML = '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
        btn.title = 'Alternar tema claro';
    } else {
        btn.innerHTML = '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>';
        btn.title = 'Alternar tema escuro';
    }
}

function toggleTheme() {
    var current = document.documentElement.getAttribute('data-theme') || 'light';
    var next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
}

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
    var theme = getPreferredTheme();
    applyTheme(theme);
    
    var contrast = getPreferredContrast();
    applyContrast(contrast);
    
    var fontSize = getPreferredFontSize();
    applyFontSize(fontSize);
    
    var btnDarkMode = document.getElementById('btn-dark-mode');
    if (btnDarkMode) {
        btnDarkMode.addEventListener('click', toggleTheme);
    }
    
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

window.ThemeToggle = { toggle: toggleTheme, apply: applyTheme };
window.AccessibilityToggle = {
    toggleContrast: toggleContrast,
    increaseFontSize: increaseFontSize,
    decreaseFontSize: decreaseFontSize,
    applyContrast: applyContrast,
    applyFontSize: applyFontSize,
};
})();