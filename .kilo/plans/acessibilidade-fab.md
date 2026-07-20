# Plano: Acessibilidade - Botão Flutuante com Funcionalidades Avançadas

## Objetivo
Adicionar um botão flutuante (FAB) no canto inferior direito, disponível em todas as páginas, que abre um painel com 4 funcionalidades de acessibilidade que o navegador não oferece nativamente. As preferências são salvas no `localStorage` e persistem entre sessões.

## Funcionalidades

### 1. Régua de Leitura
- Régua horizontal semi-transparente que segue o cursor do mouse
- Altura de ~40px, com bordas sutis na cor do sistema
- Ajuda pessoas com TDAH ou dificuldade de concentração a não perder a linha
- Toggle on/off no painel

### 2. Modo de Foco
- Escurece toda a página exceto o bloco de texto onde o mouse está
- Usa `box-shadow` com spread grande para criar o efeito de spotlight
- O elemento em foco é detectado via `document.elementFromPoint()`
- Ajuda alunos com dificuldade de atenção a focar no conteúdo atual
- Toggle on/off no painel

### 3. Fonte para Dislexia (OpenDyslexic)
- Troca a fonte do sistema para OpenDyslexic (via CDN)
- Fonte com peso visual diferente em cada letra, dificultando confusão entre b/d/p/q
- Carregada via `@font-face` no CSS com `font-display: swap`
- Toggle on/off no painel

### 4. Filtro para Daltonismo
- Filtros SVG para protanopia, deuteranopia e tritanopia
- Aplicados via `filter: url(#filtro)` no `<body>`
- Dropdown/select no painel para escolher o tipo
- Opção "Nenhum" para desativar

## Arquitetura

### Arquivos a Criar
| Arquivo | Descrição |
|---------|-----------|
| `frontend/css/acessibilidade.css` | Estilos do FAB, painel, toggles, régua, modo foco, fonte dislexia, filtros daltonismo |
| `frontend/js/acessibilidade.js` | Lógica do FAB, painel, 4 features, persistência localStorage |

### Arquivos a Modificar
| Arquivo | Modificação |
|---------|-------------|
| `frontend/painel.html` | Adicionar `<link>` CSS e `<script>` JS |
| `frontend/disciplinas.html` | Adicionar `<link>` CSS e `<script>` JS |
| `frontend/chat.html` | Adicionar `<link>` CSS e `<script>` JS |
| `frontend/portal.html` | Adicionar `<link>` CSS e `<script>` JS |
| `frontend/importacao.html` | Adicionar `<link>` CSS e `<script>` JS |
| `frontend/notificacoes.html` | Adicionar `<link>` CSS e `<script>` JS |

## Detalhamento Técnico

### CSS (`acessibilidade.css`)
- **FAB**: `position: fixed; bottom: 24px; right: 24px;` com `z-index: 9999`
- **Painel**: `position: fixed; bottom: 90px; right: 24px; width: 320px;` com animação slide-up
- **Switch toggle**: Checkbox customizado com slider
- **Régua**: `position: fixed; left: 0; right: 0; height: 40px;` com `pointer-events: none`
- **Modo Foco**: Overlay escuro + spotlight com `box-shadow: 0 0 0 9999px rgba(0,0,0,0.65)`
- **Dislexia**: `@font-face` carregando OpenDyslexic do CDN jsDelivr
- **Daltonismo**: Filtros SVG via `<filter>` com `feColorMatrix`
- **Responsivo**: Ajustes para mobile (< 480px)

### JS (`acessibilidade.js`)
- **IIFE** para encapsulamento
- **Estado**: Objeto `{ regua, foco, dislexia, daltonismo }` salvo no localStorage
- **Criação DOM**: FAB, painel, régua e spotlight criados via JS (injetados no body)
- **SVG Filters**: Injetados no body para os filtros de daltonismo
- **Event listeners**: mousemove para régua e modo foco, change para toggles
- **Persistência**: `localStorage.getItem/setItem` com chave `acolhe-acessibilidade`
- **Auto-init**: Detecta `DOMContentLoaded` ou executa imediatamente

### Estrutura do Painel
```
┌──────────────────────────────┐
│ ♿ Acessibilidade             │
├──────────────────────────────┤
│ LEITURA E FOCO               │
│ ┌──────────────────────────┐ │
│ │ 📏 Régua de Leitura  [○]│ │
│ │    Destaca a linha       │ │
│ └──────────────────────────┘ │
│ ┌──────────────────────────┐ │
│ │ 🎯 Modo de Foco      [○]│ │
│ │    Escurece o resto      │ │
│ └──────────────────────────┘ │
├──────────────────────────────┤
│ FONTE                        │
│ ┌──────────────────────────┐ │
│ │ 🔤 Fonte para Dislexia[○]│ │
│ │    OpenDyslexic          │ │
│ └──────────────────────────┘ │
├──────────────────────────────┤
│ CORES                        │
│ ┌──────────────────────────┐ │
│ │ Filtro para Daltonismo   │ │
│ │ [Nenhum          ▼]      │ │
│ │  - Protanopia            │ │
│ │  - Deuteranopia          │ │
│ │  - Tritanopia            │ │
│ └──────────────────────────┘ │
└──────────────────────────────┘
```

## Ordem de Implementação
1. Criar `frontend/css/acessibilidade.css`
2. Criar `frontend/js/acessibilidade.js`
3. Adicionar referências nas 6 páginas HTML
4. Verificar servidor inicia e testar manualmente

## Validação
- [ ] FAB aparece no canto inferior direito em todas as páginas
- [ ] Clique no FAB abre/fecha o painel com animação
- [ ] Régua de leitura segue o cursor quando ativada
- [ ] Modo de foco escurece tudo exceto o bloco sob o mouse
- [ ] Fonte OpenDyslexic é carregada e aplicada quando ativada
- [ ] Filtros de daltonismo funcionam para os 3 tipos
- [ ] Preferências persistem ao recarregar a página (localStorage)
- [ ] Painel fecha ao clicar fora ou pressionar Escape
- [ ] Responsivo em mobile
- [ ] Não interfere com outras funcionalidades do sistema

## Riscos e Mitigações
| Risco | Mitigação |
|-------|-----------|
| OpenDyslexic CDN indisponível | Usar `font-display: swap` para fallback graceful |
| Modo foco performance | Throttle do mousemove se necessário |
| Filtros SVG não suportados | Fallback: não afeta navegadores modernos |
| Conflito com modais existentes | `z-index` alto (9999) para FAB e painel |
