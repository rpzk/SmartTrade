#!/usr/bin/env python3
"""
Validador de Política de Dados Reais
Verifica se o código contém dados simulados ou mockados
"""

import re
import sys
import os
from pathlib import Path

# Padrões proibidos que indicam dados mockados/simulados
PROHIBITED_PATTERNS = [
    (r'mock_data', 'Uso de dados mockados'),
    (r'fake_data', 'Uso de dados falsos'),
    (r'simulated_price', 'Preço simulado'),
    (r'dummy_data', 'Dados dummy'),
    (r'DEMO_MODE\s*=\s*True', 'Modo demo ativado'),
    (r'SIMULATION.*=.*True', 'Modo simulação ativado'),
    (r'random\.uniform.*price', 'Geração aleatória de preços'),
    (r'random\.randint.*volume', 'Geração aleatória de volumes'),
    (r'hardcoded.*prices?.*=.*\[', 'Preços hardcoded'),
]

# Arquivos a serem verificados
INCLUDE_PATTERNS = ['*.py']
EXCLUDE_DIRS = ['.git', '__pycache__', '.venv', 'venv', 'env', 'node_modules']
EXCLUDE_FILES = ['validate_no_mock_data.py']  # Não validar a si mesmo


def check_file(filepath):
    """Verifica um arquivo em busca de padrões proibidos"""
    violations = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            for pattern, description in PROHIBITED_PATTERNS:
                for line_num, line in enumerate(lines, 1):
                    # Ignorar comentários
                    if line.strip().startswith('#'):
                        continue
                    
                    if re.search(pattern, line, re.IGNORECASE):
                        violations.append({
                            'file': str(filepath),
                            'line': line_num,
                            'pattern': pattern,
                            'description': description,
                            'content': line.strip()
                        })
    except Exception as e:
        print(f"⚠️  Erro ao ler {filepath}: {e}", file=sys.stderr)
    
    return violations


def should_check_file(filepath):
    """Determina se um arquivo deve ser verificado"""
    filepath = Path(filepath)
    
    # Verificar extensão
    if not any(filepath.match(pattern) for pattern in INCLUDE_PATTERNS):
        return False
    
    # Verificar se está em diretório excluído
    for exclude_dir in EXCLUDE_DIRS:
        if exclude_dir in filepath.parts:
            return False
    
    # Verificar se é arquivo excluído
    if filepath.name in EXCLUDE_FILES:
        return False
    
    return True


def validate_project(root_path='.'):
    """Valida todo o projeto"""
    root = Path(root_path)
    all_violations = []
    files_checked = 0
    
    print("🔍 Validando política de dados reais...")
    print(f"📁 Diretório: {root.absolute()}\n")
    
    # Procurar arquivos Python
    for filepath in root.rglob('*'):
        if filepath.is_file() and should_check_file(filepath):
            files_checked += 1
            violations = check_file(filepath)
            if violations:
                all_violations.extend(violations)
    
    # Reportar resultados
    print(f"📊 Arquivos verificados: {files_checked}\n")
    
    if all_violations:
        print("❌ VIOLAÇÕES ENCONTRADAS:\n")
        for v in all_violations:
            print(f"  Arquivo: {v['file']}")
            print(f"  Linha: {v['line']}")
            print(f"  Problema: {v['description']}")
            print(f"  Código: {v['content']}")
            print()
        
        print(f"❌ Total: {len(all_violations)} violação(ões) da política de dados reais")
        print("\n⚠️  IMPORTANTE: Este projeto NÃO deve usar dados simulados!")
        print("📖 Consulte DATA_POLICY.md para detalhes\n")
        return False
    else:
        print("✅ Nenhuma violação encontrada!")
        print("✅ Código está em conformidade com a política de dados reais\n")
        return True


if __name__ == '__main__':
    root_path = sys.argv[1] if len(sys.argv) > 1 else '.'
    success = validate_project(root_path)
    sys.exit(0 if success else 1)
