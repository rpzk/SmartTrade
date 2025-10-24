# Guia de Uso - SmartTrade

## Início Rápido

### 1. Instalação
```bash
# Clone o repositório
git clone https://github.com/rpzk/SmartTrade.git
cd SmartTrade

# Instale as dependências
pip install -r requirements.txt
```

### 2. Configuração (Opcional)
Se você deseja usar dados reais da BingX:

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env e adicione suas credenciais
# BINGX_API_KEY=sua_api_key
# BINGX_SECRET_KEY=sua_secret_key
```

**Nota**: O aplicativo funciona perfeitamente sem configuração, usando dados simulados!

### 3. Executar
```bash
python app.py
```

Abra seu navegador em `http://localhost:5000`

## Funcionalidades

### Dashboard Principal
- **Preço Atual**: Mostra o preço atual do par selecionado
- **24h Alto/Baixo**: Máxima e mínima das últimas 24 horas
- **Volume 24h**: Volume total de negociação

### Gráficos Interativos
- **Candlestick Chart**: Visualização de velas japonesas
- **Volume**: Barras de volume abaixo do gráfico principal
- **Zoom e Pan**: Arraste e use a roda do mouse para navegar
- **Hover**: Passe o mouse sobre os dados para ver detalhes

### Controles
1. **Par de Negociação**: Selecione BTC, ETH, BNB, SOL ou XRP
2. **Intervalo**: Escolha entre 1m, 5m, 15m, 30m, 1h, 4h, 1d
3. **Atualizar**: Recarrega os dados manualmente
4. **Auto-refresh**: Atualiza automaticamente a cada 30 segundos

### Executar Trades

#### Ordem de Mercado
1. Digite o par (ex: BTC-USDT)
2. Digite a quantidade (ex: 0.001)
3. Selecione "Mercado" como tipo de ordem
4. Clique em "COMPRAR" ou "VENDER"

#### Ordem Limite
1. Digite o par (ex: BTC-USDT)
2. Digite a quantidade (ex: 0.001)
3. Selecione "Limite" como tipo de ordem
4. Digite o preço desejado
5. Clique em "COMPRAR" ou "VENDER"

## Modo Demo vs Modo Real

### Modo Demo (Padrão)
- ✅ Funciona sem API keys
- ✅ Dados simulados realistas
- ✅ Perfeito para testar a interface
- ✅ Sem risco financeiro
- ⚠️ Ordens não são executadas de verdade

Quando você vê a badge laranja "⚠️ MODO DEMO - Dados simulados" no topo, está em modo demo.

### Modo Real
- 🔑 Requer API keys configuradas no `.env`
- 📊 Dados reais da BingX
- 💰 Ordens são executadas de verdade
- ⚠️ Use com cuidado e comece com valores pequenos

## Dicas de Uso

### Para Iniciantes
1. **Comece no modo demo** para familiarizar-se com a interface
2. **Observe os gráficos** em diferentes intervalos de tempo
3. **Teste diferentes pares** de negociação
4. **Pratique análise técnica** sem risco financeiro

### Para Trading Real
1. **Configure suas API keys** da BingX
2. **Teste com valores pequenos** primeiro
3. **Use stop-loss** para gerenciar riscos
4. **Monitore suas posições** regularmente
5. **Nunca invista mais do que pode perder**

## Atalhos de Teclado
- `F5`: Recarregar página
- `Ctrl+F5`: Recarregar ignorando cache

## Resolução de Problemas

### Gráfico não carrega
- Verifique sua conexão com a internet
- Atualize a página (F5)
- Tente outro navegador

### API Error
- Verifique se suas API keys estão corretas
- Confirme que as keys têm permissões necessárias
- Verifique o status da API BingX

### Dados não atualizam
- Clique no botão "Atualizar"
- Ative o "Auto-refresh"
- Verifique a console do navegador (F12) para erros

## Recursos Avançados

### Múltiplas Janelas
Você pode abrir o SmartTrade em várias abas do navegador para monitorar diferentes pares simultaneamente.

### Análise Técnica
Use os gráficos interativos para:
- Identificar tendências
- Encontrar suportes e resistências
- Análise de volumes
- Padrões de candlestick

### Integração com Outras Ferramentas
Os dados podem ser acessados via API REST:
- `GET /api/price/<symbol>`: Preço atual
- `GET /api/ticker/<symbol>`: Estatísticas 24h
- `GET /api/chart/<symbol>`: Dados do gráfico

## Suporte

Para dúvidas ou problemas:
1. Consulte o README.md
2. Verifique o SECURITY.md para questões de segurança
3. Abra uma issue no GitHub

---

**⚠️ Aviso Legal**: Trading de criptomoedas envolve riscos significativos. Use este software por sua conta e risco.
