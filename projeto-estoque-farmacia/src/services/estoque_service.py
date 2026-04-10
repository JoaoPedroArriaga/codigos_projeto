from src.models.lote import Lote

class EstoqueService:
    
    @staticmethod
    def verificar_disponibilidade(codigo_medicamento, quantidade):
        """Verifica se tem lote disponível (FEFO)"""
        print("   🔍 [DEBUG] Verificando disponibilidade:")
        print(f"      - Medicamento: {codigo_medicamento}")
        print(f"      - Quantidade: {quantidade}")
        
        lote = Lote.buscar_disponivel(codigo_medicamento, quantidade)
        
        if lote:
            print("   ✅ [DEBUG] Lote encontrado:")
            print(f"      - Número: {lote['numero_lote']}")
            print(f"      - Estoque: {lote['quantidade_atual']}")
            print(f"      - Validade: {lote['data_validade']}")
            print(f"      - Preço: R$ {lote['preco_venda']}")
            return {
                'disponivel': True,
                'lote': lote['numero_lote'],
                'validade': lote['data_validade'],
                'preco': lote['preco_venda']
            }
        else:
            print("   ❌ [DEBUG] Nenhum lote disponível")
            return {
                'disponivel': False,
                'lote': None,
                'validade': None,
                'preco': None
            }
    
    @staticmethod
    def reservar_lote(codigo_medicamento, quantidade, lote_numero):
        """Reserva um lote (não altera estoque, só valida)"""
        print("   🔍 [DEBUG] Verificando reserva:")
        print(f"      - Medicamento: {codigo_medicamento}")
        print(f"      - Lote: {lote_numero}")
        print(f"      - Quantidade: {quantidade}")
        
        lote = Lote.buscar_por_lote(codigo_medicamento, lote_numero)
        
        if not lote:
            print("   ❌ [DEBUG] Lote não encontrado")
            return {'success': False, 'error': 'Lote não encontrado'}
        
        print("   📦 [DEBUG] Lote encontrado:")
        print(f"      - Estoque atual: {lote['quantidade_atual']}")
        print(f"      - Validade: {lote['data_validade']}")
        
        if lote['quantidade_atual'] < quantidade:
            print(f"   ❌ [DEBUG] Estoque insuficiente: {lote['quantidade_atual']} < {quantidade}")
            return {'success': False, 'error': 'Estoque insuficiente'}
        
        from datetime import date
        if lote['data_validade'] < date.today():
            print(f"   ❌ [DEBUG] Lote vencido: {lote['data_validade']}")
            return {'success': False, 'error': 'Lote vencido'}
        
        print("   ✅ [DEBUG] Reserva válida")
        return {'success': True, 'id_lote': lote['id_lote']}
    
    @staticmethod
    def dar_baixa(codigo_medicamento, quantidade, lote_numero):
        """Dá baixa no estoque (diminui quantidade)"""
        print("   🔍 [DEBUG] Processando baixa:")
        print(f"      - Medicamento: {codigo_medicamento}")
        print(f"      - Lote: {lote_numero}")
        print(f"      - Quantidade: {quantidade}")
        
        lote = Lote.buscar_por_lote(codigo_medicamento, lote_numero)
        
        if not lote:
            print("   ❌ [DEBUG] Lote não encontrado")
            return {'success': False, 'error': 'Lote não encontrado'}
        
        print("   📦 [DEBUG] Lote encontrado:")
        print(f"      - Estoque atual: {lote['quantidade_atual']}")
        print(f"      - Preço: R$ {lote['preco_venda']}")
        
        if lote['quantidade_atual'] < quantidade:
            print(f"   ❌ [DEBUG] Estoque insuficiente: {lote['quantidade_atual']} < {quantidade}")
            return {'success': False, 'error': 'Estoque insuficiente'}
        
        nova_quantidade = lote['quantidade_atual'] - quantidade
        Lote.atualizar_estoque(lote['id_lote'], nova_quantidade)
        
        print("   ✅ [DEBUG] Baixa realizada:")
        print(f"      - Estoque anterior: {lote['quantidade_atual']}")
        print(f"      - Estoque novo: {nova_quantidade}")
        
        return {
            'success': True,
            'id_lote': lote['id_lote'],
            'preco_venda': lote['preco_venda']
        }