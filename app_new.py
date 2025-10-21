"""
Nova aplicação usando Application Factory - VERSÃO DEBUG
"""
from app.factory import create_app

print("🚀 Iniciando app_new.py...")

try:
    app = create_app()
    print("✅ App criada com sucesso")
    
    # Lista rotas para debug
    print("\n📋 ROTAS DISPONÍVEIS:")
    with app.app_context():
        for rule in app.url_map.iter_rules():
            print(f"   {list(rule.methods)} {rule.rule}")
    
    if __name__ == '__main__':
        print("\n🚀 Iniciando servidor na porta 5001...")
        print("🔗 Acesse: http://localhost:5001/")
        print("🔗 Health: http://localhost:5001/test/health")
        app.run(debug=True, port=5001, host='127.0.0.1')
        
except Exception as e:
    print(f"❌ Erro crítico: {e}")
    import traceback
    traceback.print_exc()