#!/bin/bash
# Script para instalar git hooks que validam a política de dados reais
# Script to install git hooks that validate the real data policy

echo "🔧 Instalando git hooks para validação de dados..."
echo "🔧 Installing git hooks for data validation..."
echo ""

# Verificar se estamos em um repositório git
if [ ! -d ".git" ]; then
    echo "❌ Erro: Este script deve ser executado na raiz do repositório git"
    echo "❌ Error: This script must be run from the git repository root"
    exit 1
fi

# Copiar pre-commit hook
if [ -f ".git-hooks/pre-commit" ]; then
    cp .git-hooks/pre-commit .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    echo "✅ Pre-commit hook instalado com sucesso!"
    echo "✅ Pre-commit hook installed successfully!"
else
    echo "❌ Erro: Arquivo .git-hooks/pre-commit não encontrado"
    echo "❌ Error: File .git-hooks/pre-commit not found"
    exit 1
fi

echo ""
echo "🎉 Configuração concluída!"
echo "🎉 Setup complete!"
echo ""
echo "ℹ️  O hook irá validar automaticamente cada commit para garantir"
echo "ℹ️  que nenhum dado simulado seja adicionado ao código."
echo ""
echo "ℹ️  The hook will automatically validate each commit to ensure"
echo "ℹ️  no simulated data is added to the code."
echo ""
echo "📖 Para mais informações, consulte DATA_POLICY.md"
echo "📖 For more information, see DATA_POLICY.md"
