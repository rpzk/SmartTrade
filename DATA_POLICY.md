# Política de Dados / Data Policy

## 🚫 Proibição de Dados Simulados

**IMPORTANTE:** Este projeto **NÃO DEVE** utilizar dados simulados, mockados ou fictícios em **NENHUMA HIPÓTESE**.

### Princípios Fundamentais

1. **Apenas Dados Reais**: Toda informação de mercado, preços, volumes e dados de trading devem vir exclusivamente da API BingX em tempo real.

2. **Sem Mocks em Produção**: Não são permitidos:
   - Dados hardcoded de preços ou volumes
   - Geradores de dados aleatórios para simular mercado
   - Valores estáticos ou pré-definidos para trading
   - Caches desatualizados sendo apresentados como dados atuais
   - Dados de exemplo ou demonstração em ambiente de produção

3. **Transparência**: O usuário deve sempre saber que está trabalhando com dados reais de mercado da BingX.

### Implementação

#### ✅ Permitido

- Buscar dados em tempo real da API BingX
- Cache temporário com timestamp visível e TTL curto (máximo 5 segundos)
- Indicadores calculados baseados em dados reais
- Histórico de dados reais da API

#### ❌ Proibido

- Gerar dados aleatórios para simular preços
- Usar valores fixos como preços de mercado
- Apresentar dados desatualizados sem aviso claro
- Modo "demo" ou "simulação" sem indicação explícita
- Fallback para dados fictícios em caso de erro de API

### Em Caso de Erro de API

Quando a API BingX não estiver disponível:

1. Exibir mensagem clara de erro
2. NÃO mostrar dados desatualizados como se fossem atuais
3. NÃO gerar dados fictícios como alternativa
4. Informar o usuário sobre a indisponibilidade do serviço

### Ambiente de Desenvolvimento

Mesmo em desenvolvimento e testes:

- Use a API de teste da BingX quando disponível
- Se precisar de dados para testes unitários, use fixtures claramente marcadas como TESTE
- Nunca commite código que gere dados fictícios para uso em produção

---

## 🚫 No Simulated Data Policy

**IMPORTANT:** This project **MUST NOT** use simulated, mocked, or fictitious data under **ANY CIRCUMSTANCES**.

### Core Principles

1. **Real Data Only**: All market information, prices, volumes, and trading data must come exclusively from the BingX API in real-time.

2. **No Production Mocks**: The following are NOT allowed:
   - Hardcoded price or volume data
   - Random data generators to simulate markets
   - Static or predefined trading values
   - Outdated caches presented as current data
   - Sample or demonstration data in production environment

3. **Transparency**: Users must always know they are working with real BingX market data.

### Implementation

#### ✅ Allowed

- Fetch real-time data from BingX API
- Temporary cache with visible timestamp and short TTL (maximum 5 seconds)
- Indicators calculated based on real data
- Historical data from the real API

#### ❌ Forbidden

- Generate random data to simulate prices
- Use fixed values as market prices
- Present outdated data without clear warning
- "Demo" or "simulation" mode without explicit indication
- Fallback to fictitious data when API errors occur

### In Case of API Errors

When BingX API is unavailable:

1. Display clear error message
2. DO NOT show outdated data as if it were current
3. DO NOT generate fictitious data as alternative
4. Inform user about service unavailability

### Development Environment

Even in development and testing:

- Use BingX test API when available
- If you need data for unit tests, use fixtures clearly marked as TEST
- Never commit code that generates fictitious data for production use
