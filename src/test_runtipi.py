#!/usr/bin/env python3
# test_runtipi.py - Script para testar a API do Runtipi

import os
import sys
import logging
from pathlib import Path
from api.runtipi import RuntipiAPI

# Configurar logging para debug
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_runtipi_api():
    """Testa a API do Runtipi"""
    
    # Configurações (ajuste conforme necessário)
    RUNTIPI_HOST = os.getenv('RUNTIPI_HOST')
    USERNAME = os.getenv('RUNTIPI_USERNAME')
    PASSWORD = os.getenv('RUNTIPI_PASSWORD')
    
    print(f"🔧 Testando conexão com Runtipi em: {RUNTIPI_HOST}")
    print(f"👤 Usuário: {USERNAME}")
    print("-" * 50)
    
    # Inicializa a API
    api = RuntipiAPI(
        host=RUNTIPI_HOST,
        username=USERNAME,
        password=PASSWORD
    )
    
    # Teste 1: Conexão básica
    print("🧪 Teste 1: Testando conexão e autenticação...")
    if api.test_connection():
        print("✅ Conexão OK")
    else:
        print("❌ Falha na conexão")
        return False
    
    # Teste 2: Listar apps instalados
    print("\n🧪 Teste 2: Listando apps instalados...")
    apps_data = api.get_installed_apps()
    
    if apps_data:
        print("✅ Apps obtidos com sucesso")
        
        if 'installed' in apps_data:
            apps = apps_data['installed']
            print(f"📱 Total de apps: {len(apps)}")
            
            for app in apps[:5]:  # Mostra apenas os primeiros 5
                app_id = app['info']['id']
                app_name = app['info'].get('name', app_id)
                status = app['app']['status']
                print(f"  • {app_id} ({app_name}): {status}")
                
            if len(apps) > 5:
                print(f"  ... e mais {len(apps) - 5} apps")
        else:
            print("⚠️ Estrutura de dados inesperada:")
            print(f"Keys disponíveis: {list(apps_data.keys())}")
    else:
        print("❌ Falha ao obter apps")
        return False
    
    # Teste 3: Status de um app específico (se existir)
    if apps_data and 'installed' in apps_data and apps_data['installed']:
        first_app = apps_data['installed'][0]
        app_id = first_app['info']['id']
        
        print(f"\n🧪 Teste 3: Verificando status do app '{app_id}'...")
        app_status = api.get_app_status(app_id)
        
        if app_status:
            print("✅ Status obtido com sucesso")
            print(f"  Status: {app_status.get('app', {}).get('status', 'N/A')}")
        else:
            print("❌ Falha ao obter status do app")
    
    print("\n🎉 Todos os testes concluídos!")
    return True

if __name__ == "__main__":
    try:
        success = test_runtipi_api()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Teste interrompido pelo usuário")
        exit(1)
    except Exception as e:
        print(f"\n💥 Erro inesperado: {e}")
        exit(1)