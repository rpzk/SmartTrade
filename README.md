# 📊 SmartTrade

Aplicativo moderno de trading que utiliza a API do BingX para executar trades com gráficos modernos e funcionais.

## 🚀 Recursos

- **Interface moderna e intuitiva** com design responsivo
- **Gráficos interativos** usando Plotly com candlesticks e volume
- **Trading em tempo real** com suporte a ordens de mercado e limite
- **Monitoramento de preços** com estatísticas de 24h
- **Auto-refresh** para atualização automática dos dados
- **Múltiplos pares de trading** (BTC, ETH, BNB, SOL, XRP e mais)
- **Diferentes intervalos de tempo** (1m, 5m, 15m, 30m, 1h, 4h, 1d)

## 📋 Pré-requisitos

- Python 3.8 ou superior
- Conta na BingX com API key e Secret key

## 🔧 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/rpzk/SmartTrade.git
cd SmartTrade
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure suas credenciais da API BingX:
```bash
cp .env.example .env
```

4. Edite o arquivo `.env` e adicione suas credenciais:
```
BINGX_API_KEY=sua_api_key_aqui
BINGX_SECRET_KEY=sua_secret_key_aqui
BINGX_BASE_URL=https://open-api.bingx.com
```

## 🎯 Como Usar

1. Inicie o aplicativo:
```bash
python app.py
```

2. Abra seu navegador e acesse:
```
http://localhost:5000
```

3. Use a interface para:
   - Visualizar gráficos de preços em tempo real
   - Monitorar estatísticas de mercado
   - Executar ordens de compra e venda
   - Alternar entre diferentes pares de trading
   - Ajustar intervalos de tempo dos gráficos

## 📊 Funcionalidades

### Gráficos
- Candlestick charts interativos
- Visualização de volume
- Múltiplos intervalos de tempo
- Zoom e pan nos gráficos

### Trading
- Ordens de mercado (execução imediata)
- Ordens limitadas (com preço específico)
- Compra e venda com interface simples
- Validação de dados antes da execução

### Monitoramento
- Preço atual em tempo real
- Máxima e mínima de 24h
- Volume de negociação
- Variação percentual de preço

## 🔐 Segurança

- Nunca compartilhe suas API keys
- Use o arquivo `.env` para armazenar credenciais (já está no .gitignore)
- Recomenda-se usar API keys com permissões limitadas apenas para trading
- Sempre teste com quantidades pequenas primeiro

## 📁 Estrutura do Projeto

```
SmartTrade/
├── app.py              # Aplicação Flask principal
├── bingx_api.py        # Cliente da API BingX
├── requirements.txt    # Dependências Python
├── .env.example        # Exemplo de configuração
├── templates/
│   └── index.html     # Interface web
└── README.md          # Documentação
```

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python, Flask
- **Frontend:** HTML5, CSS3, JavaScript
- **Gráficos:** Plotly.js
- **API:** BingX REST API
- **Gerenciamento de Ambiente:** python-dotenv

## 📝 API Endpoints

- `GET /` - Dashboard principal
- `GET /api/price/<symbol>` - Obtém preço atual
- `GET /api/ticker/<symbol>` - Obtém estatísticas 24h
- `GET /api/chart/<symbol>` - Obtém dados para gráficos
- `GET /api/pairs` - Lista pares disponíveis
- `GET /api/balance` - Obtém saldo da conta
- `GET /api/orders` - Lista ordens abertas
- `POST /api/trade` - Executa uma ordem

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e pull requests.

## 📄 Licença

Este projeto é de código aberto e está disponível sob a licença MIT.

## ⚠️ Aviso Legal

Este software é fornecido "como está", sem garantias de qualquer tipo. Trading de criptomoedas envolve riscos significativos. Use por sua conta e risco.