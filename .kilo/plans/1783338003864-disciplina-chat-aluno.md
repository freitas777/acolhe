# Plano: Cache de Respostas da IA (Conteúdo Educacional)

## Objetivo
Reduzir custo e latência cacheando respostas de `gerar_conteudo_educacional()` quando o mesmo prompt (tema + perfil) é gerado novamente.

## Decisões de Design
- **Escopo**: apenas `gerar_conteudo_educacional()` — chat é muito contextual para cache eficaz
- **Chave**: SHA256 do prompt completo (hash exato)
- **Armazenamento**: em memória (OrderedDict LRU), consistente com padrão atual do sistema
- **Invalidação**: TTL de 24h + LRU (remove mais antigo quando cache cheio)

## Configuração
**Arquivo:** `backend/config.py`
```python
ai_cache_max_size: int = 200
ai_cache_ttl_seconds: int = 86400  # 24 horas
```

## Implementação

### 1. Config — `backend/config.py`
Adicionar duas settings:
- `ai_cache_max_size: int = 200` — máximo de entradas no cache
- `ai_cache_ttl_seconds: int = 86400` — TTL em segundos (24h)

### 2. Service — `backend/services/ai_service.py`
Adicionar no `__init__`:
```python
self._cache: OrderedDict[str, tuple[str, float]] = OrderedDict()  # chave -> (resposta, timestamp)
```

Adicionar métodos privados:
```python
def _cache_get(self, chave: str) -> str | None:
    """Retorna resposta cacheada se existir e não expirada."""
    if chave in self._cache:
        resposta, timestamp = self._cache[chave]
        if time.time() - timestamp < settings.ai_cache_ttl_seconds:
            self._cache.move_to_end(chave)
            logger.info("Cache HIT: %s", chave[:16])
            return resposta
        else:
            del self._cache[chave]
            logger.info("Cache EXPIRED: %s", chave[:16])
    return None

def _cache_set(self, chave: str, resposta: str) -> None:
    """Armazena resposta no cache, removendo mais antigo se cheio."""
    self._cache[chave] = (resposta, time.time())
    self._cache.move_to_end(chave)
    while len(self._cache) > settings.ai_cache_max_size:
        chave_antiga = next(iter(self._cache))
        del self._cache[chave_antiga]
    logger.info("Cache SET: %s (total=%d)", chave[:16], len(self._cache))
```

Modificar `gerar_conteudo_educacional()`:
```python
async def gerar_conteudo_educacional(self, tema: str, perfil_aluno: dict) -> str:
    prompt = self._construir_prompt_educacional(tema, perfil_aluno)
    chave = hashlib.sha256(prompt.encode()).hexdigest()

    # Verifica cache
    cached = self._cache_get(chave)
    if cached:
        return cached

    # Gera conteúdo
    modelo = self._obter_modelo()
    loop = asyncio.get_running_loop()
    resposta = await loop.run_in_executor(
        None, lambda: modelo.generate_content(prompt)
    )

    # Armazena no cache
    self._cache_set(chave, resposta.text)
    return resposta.text
```

### 3. Testes — `testes/test_ai_service.py`
Adicionar testes:
- `test_cache_hit_retorna_mesma_resposta` — gera 2x com mesmo input, segunda chamada não invoca API
- `test_cache_miss_gera_nova_resposta` — inputs diferentes geram respostas diferentes
- `test_cache_ttl_expira` — mock time.time() para simular expiração
- `test_cache_lru_remove_mais_antigo` — preenche cache além do limite, verifica remoção

## Arquivos Afetados

| Arquivo | Ação |
|---------|------|
| `backend/config.py` | Adicionar `ai_cache_max_size` e `ai_cache_ttl_seconds` |
| `backend/services/ai_service.py` | Adicionar cache LRU+TTL em `gerar_conteudo_educacional()` |
| `testes/test_ai_service.py` | Adicionar testes de cache |

## Ordem de Implementação
1. Config (settings de cache)
2. Service (cache LRU+TTL no `gerar_conteudo_educacional`)
3. Testes (hit, miss, TTL, LRU)
4. Verificar servidor inicia e testes passam

## Validação
- [ ] Primeira chamada gera conteúdo via API
- [ ] Segunda chamada com mesmo tema+perfil retorna do cache (sem chamada à API)
- [ ] Chamada com tema diferente gera novo conteúdo
- [ ] Cache expira após TTL configurado
- [ ] Cache remove entradas antigas quando atinge limite
- [ ] Logs mostram HIT/MISS/EXPIRED/SET
- [ ] Servidor inicia sem erros

## Riscos e Mitigações

| Risco | Mitigação |
|-------|-----------|
| Cache ocupa muita memória | Limite de 200 entradas (~200KB-2MB típico) |
| Resposta desatualizada | TTL de 24h garante renovação diária |
| Thread safety | `AIService` é singleton, mas `_cache` não tem lock — acceptable pois `OrderedDict` é atomic para operações simples em CPython (GIL) |
| Perde cache ao reiniciar | Comportamento esperado — cache em memória é volátil |
