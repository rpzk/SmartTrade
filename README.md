# SmartTrade

## 🚨 Política de Dados Reais

**ATENÇÃO:** Este aplicativo utiliza **EXCLUSIVAMENTE dados reais** da API BingX. 

❌ **NÃO há dados simulados, mockados ou fictícios.**

Para detalhes completos, consulte [DATA_POLICY.md](DATA_POLICY.md).

---

## Sobre o Projeto

SmartTrade é uma aplicação de trading que integra com a exchange BingX, fornecendo dados de mercado em tempo real e funcionalidades de trading com gráficos modernos.

### Características Principais

- ✅ Dados 100% reais da API BingX
- 📊 Gráficos de preços em tempo real
- 💹 Execução de ordens de compra e venda
- 📈 Análise de mercado com dados históricos autênticos
- 🔐 Integração segura com API keys

## 🛡️ Garantia de Qualidade de Dados

Este projeto inclui ferramentas automáticas para garantir que **nenhum dado simulado** seja adicionado:

### Validação Manual

```bash
# Validar o código antes de commit
python3 validate_no_mock_data.py
```

### Instalar Git Hooks (Recomendado)

```bash
# Instalar hook que valida automaticamente cada commit
./setup-hooks.sh
```

### CI/CD Automático

O projeto inclui workflow GitHub Actions que valida automaticamente cada PR para garantir conformidade com a política de dados reais.

## 📚 Documentação

- **[DATA_POLICY.md](DATA_POLICY.md)** - Política completa sobre uso de dados reais
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Guia de contribuição com exemplos práticos
- **[.no-mock-data](.no-mock-data)** - Configuração de padrões proibidos

## 🔍 Para Desenvolvedores

Antes de fazer commit:

1. ✅ Execute `python3 validate_no_mock_data.py`
2. ✅ Leia [DATA_POLICY.md](DATA_POLICY.md)
3. ✅ Use apenas dados reais da API BingX
4. ✅ Não use fallback para dados fictícios em caso de erro

**Lembre-se:** Em caso de dúvida sobre dados, sempre prefira a API real!