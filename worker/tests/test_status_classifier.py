from app.services.status_classifier_service import status_classifier_service


def test_classificador_move_novo_para_qualificando_quando_lead_informa_evento():
    """AC 2 (story 6.6): lead informa evento/peça/data → novo vira qualificando."""
    destino, motivo = status_classifier_service.classificar_transicao(
        status_atual="novo",
        mensagens_lead=["É um casamento e quero um terno azul marinho completo"],
        texto_resposta_ia="Encontrei ótimas opções de terno para você.",
    )
    assert destino == "qualificando"
    assert motivo


def test_classificador_nao_move_novo_sem_sinal_algum():
    destino, motivo = status_classifier_service.classificar_transicao(
        status_atual="novo",
        mensagens_lead=["Oi tudo bem?"],
        texto_resposta_ia="Oi! Como posso te ajudar hoje?",
    )
    assert destino is None
    assert motivo is None


def test_classificador_move_para_orcamento_quando_lead_pergunta_preco():
    """AC 3: pergunta de preço/orçamento do lead move para orçamento (a partir de novo/qualificando)."""
    destino, motivo = status_classifier_service.classificar_transicao(
        status_atual="qualificando",
        mensagens_lead=["Quanto custa o aluguel desse terno?"],
        texto_resposta_ia="Deixa eu confirmar os detalhes pra te passar o valor certinho.",
    )
    assert destino == "orcamento"


def test_classificador_move_para_orcamento_quando_ia_responde_com_valor_real():
    """AC 3: mesmo sem o lead perguntar explicitamente, um valor real (R$) na resposta da IA conta."""
    destino, motivo = status_classifier_service.classificar_transicao(
        status_atual="novo",
        mensagens_lead=["Quero ver ternos para o casamento"],
        texto_resposta_ia="O aluguel desse terno é R$ 450,00.",
    )
    assert destino == "orcamento"


def test_classificador_nao_move_orcamento_quando_ja_passou_dessa_etapa():
    """Nunca reclassifica um lead que já avançou além de orçamento no funil."""
    destino, motivo = status_classifier_service.classificar_transicao(
        status_atual="negociando",
        mensagens_lead=["Quanto custa mesmo?"],
        texto_resposta_ia="É R$ 450,00.",
    )
    assert destino is None


def test_classificador_move_follow_up_para_negociando_ao_responder():
    """AC 4: lead em follow_up que responde volta para negociando, qualquer que seja a mensagem."""
    destino, motivo = status_classifier_service.classificar_transicao(
        status_atual="follow_up",
        mensagens_lead=["Oi, ainda tenho interesse sim"],
        texto_resposta_ia="Que bom! Vamos continuar então.",
    )
    assert destino == "negociando"
    assert motivo


def test_classificador_nao_reclassifica_lead_ja_qualificado_sem_sinal_de_preco():
    """Lead já qualificando, sem sinal de preço/orçamento — classificador não propõe nada."""
    destino, motivo = status_classifier_service.classificar_transicao(
        status_atual="qualificando",
        mensagens_lead=["Prefiro tamanho 42"],
        texto_resposta_ia="Anotado, tamanho 42.",
    )
    assert destino is None
