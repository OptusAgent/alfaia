import json
import pytest
from app.services.ai_engine import AIEngineService
from app.services.context_builder import ContatoDTO, LeadDTO
from app.services.tools_registry import tools_registry
from app.services.lead_service import LeadService, LeadModel
from app.services.openrouter_client import LLMRespostaDTO, LLMToolCallDTO


def test_registro_das_8_tools_schemas_validados():
    """Testa se todas as 8 ferramentas de PRD §8.2 estão registradas com schemas validados (AC 5)."""
    esperadas = [
        "buscar_produtos",
        "consultar_slots",
        "agendar",
        "atualizar_lead",
        "mover_status",
        "registrar_interesse",
        "abrir_transbordo",
        "encerrar",
    ]

    for tool_name in esperadas:
        assert tool_name in tools_registry.ferramentas

    # Teste de execução rápida de cada uma com parâmetros válidos
    ctx = {"tenant_id": "tenant_piloto", "lead": LeadModel(id="l1", tenant_id="t1", contato_id="c1")}
    assert tools_registry.executar_tool("buscar_produtos", {"evento": "casamento"}, ctx)["sucesso"] is True
    assert tools_registry.executar_tool("consultar_slots", {"tipo": "prova", "data_inicio": "2026-09-01"}, ctx)["sucesso"] is True
    assert tools_registry.executar_tool("agendar", {"tipo": "prova", "data": "2026-09-01", "hora": "14:00"}, ctx)["sucesso"] is True
    assert tools_registry.executar_tool("atualizar_lead", {"tamanho": "42"}, ctx)["sucesso"] is True
    assert tools_registry.executar_tool("abrir_transbordo", {"motivo": "teste"}, ctx)["sucesso"] is True


def test_motor_nunca_gera_menu_numerico():
    """Testa sanitização para garantir que a IA nunca gera menus numéricos (AC 4, AC 19.2 item 1)."""
    raw_response = "Olá! Escolha uma opção:\n1. Ver catálogo\n2) Agendar prova\n• Falar com atendente"
    sanitizado = AIEngineService.sanitizar_resposta_ia(raw_response)

    assert "digite 1" not in sanitizado.lower()
    assert "escolha uma opção" not in sanitizado.lower()
    assert "1. Ver catálogo" not in sanitizado
    assert "2)" not in sanitizado
    assert "•" not in sanitizado
    assert "Ver catálogo" not in sanitizado
    assert "Agendar prova" not in sanitizado
    assert "Falar com atendente" not in sanitizado
    assert sanitizado == "Olá!"


def test_motor_preserva_horarios_reais_mesmo_formatados_como_lista():
    """
    Regressão do achado real em produção (2026-08-21): a IA listou os horários disponíveis com
    bullet/quebra de linha por item ("- 09:00\\n- 11:00\\n- 14:00") e a sanitização de menu
    apagava a lista inteira, deixando "temos os seguintes horários disponíveis:" seguido de nada
    — o lead nunca via os horários de verdade. Uma linha de "menu" com horário/valor real (P3)
    agora vira frase corrida, nunca é apagada.
    """
    raw_response = (
        "Para amanhã, dia 21/08, temos os seguintes horários disponíveis para a prova do "
        "Terno Areia Rústico:\n"
        "- 09:00\n- 11:00\n- 14:00\n"
        "Qual desses horários funciona melhor para você?"
    )
    sanitizado = AIEngineService.sanitizar_resposta_ia(raw_response)

    assert "09:00" in sanitizado
    assert "11:00" in sanitizado
    assert "14:00" in sanitizado
    assert "- 09:00" not in sanitizado
    assert "Qual desses horários funciona melhor para você?" in sanitizado


def test_motor_preserva_lista_numerada_de_catalogo_com_codigo_real():
    """
    Ajuste de produto (reversão, 2026-08-21): a lista numerada de catálogo no formato mandado
    ("N - cód. X - descrição — cor — tamanhos ...") é a única lista numerada intencional — precisa
    sobreviver intacta à sanitização de menu, diferente de um menu de ação fake ("1. Ver catálogo").
    """
    raw_response = (
        "Encontrei essas opções de terno:\n"
        "1 - cód. T-203 - Terno Linho Praia Champanhe — Bege Claro — tamanhos 46, 48, 50\n"
        "2 - cód. T-202 - Terno Areia Rústico 3 Peças — Bege Areia — tamanhos 46, 48, 52\n"
        "Quer ver a imagem de qual dos itens acima? Digite o número do item ou o código. Se "
        "quiser ver mais de um, separe por vírgula (ex.: 1,2) ou digite \"todos\"."
    )
    sanitizado = AIEngineService.sanitizar_resposta_ia(raw_response)

    assert "1 - cód. T-203 - Terno Linho Praia Champanhe" in sanitizado
    assert "2 - cód. T-202 - Terno Areia Rústico 3 Peças" in sanitizado
    assert "Digite o número do item ou o código" in sanitizado


def test_motor_ainda_remove_lista_de_acao_sem_dado_real():
    """Uma lista sem dado real (horário/valor) continua sendo removida por inteiro, não naturalizada."""
    raw_response = "Posso te ajudar assim:\n1. Ver catálogo\n2. Agendar prova\nO que prefere?"
    sanitizado = AIEngineService.sanitizar_resposta_ia(raw_response)

    assert "Ver catálogo" not in sanitizado
    assert "Agendar prova" not in sanitizado
    assert "O que prefere?" in sanitizado


def test_motor_substitui_menu_puro_por_pergunta_natural():
    raw_response = "Escolha uma opção:\n1. Ver catálogo\n2) Agendar prova\n1️⃣ Falar com atendente"
    sanitizado = AIEngineService.sanitizar_resposta_ia(raw_response)

    assert "Ver catálogo" not in sanitizado
    assert "Agendar prova" not in sanitizado
    assert "1️⃣" not in sanitizado
    assert sanitizado == "Me diga como prefere seguir e eu continuo por aqui."


def test_motor_remove_markdown_de_imagem_da_resposta():
    """
    Regressão do achado real em produção (2026-08-21): a IA às vezes tenta "mostrar" a foto ela
    mesma inserindo sintaxe markdown de imagem na resposta — o WhatsApp não renderiza isso, o
    lead só vê um link quebrado. A foto já vai de verdade via enviar_midia; o texto nunca deveria
    conter a URL/sintaxe de imagem.
    """
    raw_response = (
        "Aqui estão os detalhes do Terno Linho Praia Champanhe (T-203):\n"
        "![Terno Linho Praia Champanhe](https://irewoqkwywsapiiytdau.supabase.co/storage/v1/object/public/wl-mock-catalogo/TERNOMASCULINO002.jpg)\n"
        "Gostou desse terno ou gostaria de ver mais opções?"
    )
    sanitizado = AIEngineService.sanitizar_resposta_ia(raw_response)

    assert "![" not in sanitizado
    assert "supabase.co" not in sanitizado
    assert "Aqui estão os detalhes do Terno Linho Praia Champanhe (T-203)" in sanitizado
    assert "Gostou desse terno ou gostaria de ver mais opções?" in sanitizado


def test_motor_nunca_pede_cpf_ou_documento():
    """Testa sanitização para garantir que a IA nunca solicita CPF ou fotos de documento (AC 7, AC 19.2 item 8)."""
    raw_response = "Para confirmar seu agendamento, envie seu CPF e foto do documento."
    sanitizado = AIEngineService.sanitizar_resposta_ia(raw_response)

    assert "cpf" not in sanitizado.lower()
    assert "foto do documento" not in sanitizado.lower()


def test_erro_ferramenta_aciona_transbordo_sem_inventar_dado():
    """Testa se erro/timeout em chamada de ferramenta aciona transbordo sem inventar dados (AC 3, P3)."""
    engine = AIEngineService()
    lead_service = LeadService()

    contato = ContatoDTO(id="cnt_1", tenant_id="t1", telefone="5585988112233", primeiro_contato_em="2026-08-10")
    lead = LeadModel(id="lead_1", tenant_id="t1", contato_id="cnt_1")

    res = engine.processar_atendimento(
        tenant_id="t1",
        contato_dto=contato,
        lead_dto=lead,
        tipo_entrada="primeiro_contato",
        mensagens_inbound=["Quero ver o catálogo"],
        lead_service=lead_service,
        simular_erro_tool=True,
    )

    assert res.transbordo_acionado is True
    assert "abrir_transbordo" in res.tools_executadas
    assert "Não consegui verificar os dados" in res.texto_resposta


def test_motor_usa_openrouter_quando_llm_responde():
    """Story 4.8, AC 7: sem tool_calls, o comportamento continua igual — texto direto."""
    class FakeLLM:
        def gerar_resposta(self, **kwargs):
            assert kwargs["modelo"] == "openai/gpt-4o-mini"
            assert "prompt_sistema" in kwargs
            assert "tools" in kwargs and len(kwargs["tools"]) == 8
            return LLMRespostaDTO(content="Claro, posso te ajudar com uma prova para casamento.")

    engine = AIEngineService(llm_client=FakeLLM())
    contato = ContatoDTO(id="cnt_1", tenant_id="t1", telefone="5585988112233", primeiro_contato_em="2026-08-10")
    lead = LeadModel(id="lead_1", tenant_id="t1", contato_id="cnt_1")

    res = engine.processar_atendimento(
        tenant_id="t1",
        contato_dto=contato,
        lead_dto=lead,
        tipo_entrada="primeiro_contato",
        mensagens_inbound=["Oi"],
        ia_config={"modelo": "openai/gpt-4o-mini"},
    )

    assert res.texto_resposta == "Claro, posso te ajudar com uma prova para casamento."
    assert res.tools_executadas == []


def test_motor_executa_tool_calls_reais_antes_da_resposta_final():
    """Story 4.8, AC 2, AC 4: com tool_calls, executa a tool de verdade e usa o resultado real na resposta final."""
    chamadas = {"n": 0}

    class FakeLLMComToolCall:
        def gerar_resposta(self, **kwargs):
            chamadas["n"] += 1
            if chamadas["n"] == 1:
                # Primeira rodada: o modelo decide chamar buscar_produtos
                return LLMRespostaDTO(
                    content=None,
                    tool_calls=[
                        LLMToolCallDTO(id="call_1", nome="buscar_produtos", argumentos={"evento": "casamento", "tamanho": "42"})
                    ],
                )
            # Segunda rodada: já recebeu o resultado real da tool via mensagem "tool"
            mensagens = kwargs["mensagens"]
            assert mensagens[-1]["role"] == "tool"
            assert mensagens[-1]["tool_call_id"] == "call_1"
            assert '"sucesso"' in mensagens[-1]["content"]
            return LLMRespostaDTO(content="Temos ótimas opções para o seu casamento, baseadas no catálogo real.")

    engine = AIEngineService(llm_client=FakeLLMComToolCall())
    contato = ContatoDTO(id="cnt_1", tenant_id="t1", telefone="5585988112233", primeiro_contato_em="2026-08-10")
    lead = LeadModel(id="lead_1", tenant_id="t1", contato_id="cnt_1")

    res = engine.processar_atendimento(
        tenant_id="t1",
        contato_dto=contato,
        lead_dto=lead,
        tipo_entrada="primeiro_contato",
        mensagens_inbound=["Quero um vestido para casamento"],
    )

    assert res.texto_resposta == "Temos ótimas opções para o seu casamento, baseadas no catálogo real."
    assert "buscar_produtos" in res.tools_executadas
    assert chamadas["n"] == 2


def test_motor_falha_de_tool_aciona_transbordo_sem_inventar_resultado():
    """Story 4.8, AC 5: falha de tool durante o loop nunca vira resposta inventada."""
    class FakeLLMComToolQueFalha:
        def gerar_resposta(self, **kwargs):
            return LLMRespostaDTO(
                content=None,
                tool_calls=[LLMToolCallDTO(id="call_1", nome="consultar_slots", argumentos={})],
            )

    engine = AIEngineService(llm_client=FakeLLMComToolQueFalha())
    contato = ContatoDTO(id="cnt_1", tenant_id="t1", telefone="5585988112233", primeiro_contato_em="2026-08-10")
    lead = LeadModel(id="lead_1", tenant_id="t1", contato_id="cnt_1")

    # ConsultarSlotsInput exige "tipo" e "data_inicio" — sem eles, a validação Pydantic falha
    # dentro de executar_tool, retornando sucesso=False via o catch genérico do dispatcher.
    res = engine.processar_atendimento(
        tenant_id="t1",
        contato_dto=contato,
        lead_dto=lead,
        tipo_entrada="primeiro_contato",
        mensagens_inbound=["Quero marcar uma prova"],
    )

    assert res.transbordo_acionado is True
    assert "abrir_transbordo" in res.tools_executadas
    assert "Não consegui confirmar" in res.texto_resposta


def test_motor_loop_de_tool_calling_respeita_limite_de_iteracoes():
    """Story 4.8, AC 3: modelo insistindo em chamar tool sem nunca concluir aciona transbordo, não trava."""
    class FakeLLMLoopInfinito:
        def gerar_resposta(self, **kwargs):
            return LLMRespostaDTO(
                content=None,
                tool_calls=[LLMToolCallDTO(id="call_x", nome="registrar_interesse", argumentos={})],
            )

    engine = AIEngineService(llm_client=FakeLLMLoopInfinito())
    contato = ContatoDTO(id="cnt_1", tenant_id="t1", telefone="5585988112233", primeiro_contato_em="2026-08-10")
    lead = LeadModel(id="lead_1", tenant_id="t1", contato_id="cnt_1")

    res = engine.processar_atendimento(
        tenant_id="t1",
        contato_dto=contato,
        lead_dto=lead,
        tipo_entrada="primeiro_contato",
        mensagens_inbound=["Oi"],
        lead_service=None,
    )

    # registrar_interesse falha sem lead_service no contexto -> primeira iteração já aciona transbordo,
    # o que já comprova que o loop nunca deixa a conversa sem resposta. Verifica isoladamente o guard
    # de iteração chamando o loop diretamente com uma tool que "sempre funciona".
    assert res.transbordo_acionado is True

    resultados_loop = []

    class FakeLLMSempreChamaTool:
        def gerar_resposta(self, **kwargs):
            resultados_loop.append(1)
            return LLMRespostaDTO(
                content=None,
                tool_calls=[LLMToolCallDTO(id=f"call_{len(resultados_loop)}", nome="atualizar_lead", argumentos={})],
            )

    engine2 = AIEngineService(llm_client=FakeLLMSempreChamaTool())
    texto, transbordo = engine2._processar_tool_calling_loop(
        modelo="openai/gpt-4o-mini",
        prompt_sistema="sistema",
        mensagens_llm=[{"role": "user", "content": "oi"}],
        temperatura=0.3,
        ctx_exec={"tenant_id": "t1", "lead": lead, "lead_service": None, "conversa": {"estado": "ia"}},
        tools_executadas=[],
        midias_sugeridas=[],
    )

    assert transbordo is True
    assert len(resultados_loop) == AIEngineService.MAX_TOOL_CALL_ITERATIONS


def test_motor_loop_reserva_ultima_iteracao_para_resposta_final_sem_tools():
    """
    Architect Gate 4.8 (follow-up obrigatório): se as tools já resolveram o pedido mas o modelo
    ainda não formulou o texto final ao chegar na última iteração, o loop força uma chamada sem
    `tools` em vez de estourar o limite com o agendamento/ação já concluído e responder com
    "vou confirmar com a equipe" de forma enganosa.
    """
    chamadas = []

    class FakeLLMResolveNaUltima:
        def gerar_resposta(self, **kwargs):
            chamadas.append(kwargs.get("tools"))
            if len(chamadas) < AIEngineService.MAX_TOOL_CALL_ITERATIONS:
                return LLMRespostaDTO(
                    content=None,
                    tool_calls=[LLMToolCallDTO(id=f"call_{len(chamadas)}", nome="atualizar_lead", argumentos={})],
                )
            return LLMRespostaDTO(content="Prontinho, já anotei aqui!", tool_calls=[])

    engine = AIEngineService(llm_client=FakeLLMResolveNaUltima())
    lead = LeadModel(id="lead_1", tenant_id="t1", contato_id="cnt_1")

    texto, transbordo = engine._processar_tool_calling_loop(
        modelo="openai/gpt-4o-mini",
        prompt_sistema="sistema",
        mensagens_llm=[{"role": "user", "content": "oi"}],
        temperatura=0.3,
        ctx_exec={"tenant_id": "t1", "lead": lead, "lead_service": None, "conversa": {"estado": "ia"}},
        tools_executadas=[],
        midias_sugeridas=[],
    )

    assert transbordo is False
    assert texto == "Prontinho, já anotei aqui!"
    assert len(chamadas) == AIEngineService.MAX_TOOL_CALL_ITERATIONS
    assert chamadas[-1] is None  # última chamada forçada sem tools
    assert all(c is not None for c in chamadas[:-1])  # demais chamadas com tools normalmente


def test_motor_llm_configurado_mas_chamada_falha_nunca_cai_no_keyword_match_hardcoded():
    """
    Regressão do achado real em produção (2026-08-20): modelo configurado sem suporte a tool use
    na OpenRouter faz `gerar_resposta` retornar `None` mesmo com `OPENROUTER_API_KEY` presente.
    Antes deste fix, esse caso caía no `elif "casamento" in texto_inbound...` (código legado,
    hardcoded), oferecendo sempre o mesmo vestido/tamanho e ignorando o que o lead pediu de fato.
    Agora precisa cair no mesmo caminho seguro de `simular_erro_tool` — transbordo, sem inventar
    produto nem assumir gênero.
    """
    class FakeLLMConfiguradoMasFalha:
        configurado = True

        def gerar_resposta(self, **kwargs):
            return None

    engine = AIEngineService(llm_client=FakeLLMConfiguradoMasFalha())
    contato = ContatoDTO(id="cnt_1", tenant_id="t1", telefone="5585988112233", primeiro_contato_em="2026-08-10")
    lead = LeadDTO(id="lead_1", tenant_id="t1", contato_id="cnt_1", status="novo")

    res = engine.processar_atendimento(
        tenant_id="t1",
        contato_dto=contato,
        lead_dto=lead,
        tipo_entrada="primeiro_contato",
        mensagens_inbound=["CASAMENTO"],
    )

    assert res.transbordo_acionado is True
    assert "abrir_transbordo" in res.tools_executadas
    assert "buscar_produtos" not in res.tools_executadas
    assert "vestido" not in res.texto_resposta.lower()
    assert "tamanho 42" not in res.texto_resposta.lower()


def test_motor_continuacao_usa_historico_sem_reperguntar_evento_peca():
    engine = AIEngineService(
        llm_client=type("NoLLM", (), {"gerar_resposta": lambda self, **kwargs: None, "configurado": False})()
    )
    contato = ContatoDTO(id="cnt_1", tenant_id="t1", nome="Mariana", telefone="5585988112233", primeiro_contato_em="2026-08-10")
    lead = LeadDTO(id="lead_1", tenant_id="t1", contato_id="cnt_1", status="qualificando")

    historico = [
        {"remetente": "lead", "texto": "Oi"},
        {"remetente": "lead", "texto": "Quero agendar uma prova"},
        {"remetente": "lead", "texto": "É um casamento e quero um terno azul marinho completo"},
    ]

    res = engine.processar_atendimento(
        tenant_id="t1",
        contato_dto=contato,
        lead_dto=lead,
        tipo_entrada="continuacao",
        mensagens_inbound=["Dia 21 de agosto"],
        historico_mensagens=historico,
    )

    texto = res.texto_resposta.lower()
    assert "casamento" in texto
    assert "terno azul marinho" in texto
    assert "21 de agosto" in texto
    assert "com terno azul marinho completo dia" not in texto
    assert "com terno azul marinho completo no dia 21 de agosto" in texto
    assert "qual evento" not in texto
    assert "qual peça" not in texto
    assert "olá" not in texto
    assert "1." not in texto


def test_motor_envia_historico_real_para_llm_sem_duplicar_mensagem_atual():
    class FakeLLM:
        def gerar_resposta(self, **kwargs):
            mensagens = kwargs["mensagens"]
            assert mensagens == [
                {"role": "user", "content": "Quero agendar uma prova"},
                {"role": "assistant", "content": "Claro, para qual evento?"},
                {"role": "user", "content": "Casamento"},
            ]
            assert "HISTÓRICO RECENTE REAL" in kwargs["prompt_sistema"]
            return LLMRespostaDTO(content="Perfeito, seguimos com o casamento.")

    engine = AIEngineService(llm_client=FakeLLM())
    contato = ContatoDTO(id="cnt_1", tenant_id="t1", nome="Mariana", telefone="5585988112233", primeiro_contato_em="2026-08-10")
    lead = LeadDTO(id="lead_1", tenant_id="t1", contato_id="cnt_1", status="qualificando")

    res = engine.processar_atendimento(
        tenant_id="t1",
        contato_dto=contato,
        lead_dto=lead,
        tipo_entrada="continuacao",
        mensagens_inbound=["Casamento"],
        historico_mensagens=[
            {"remetente": "lead", "texto": "Quero agendar uma prova"},
            {"remetente": "ia", "texto": "Claro, para qual evento?"},
            {"remetente": "lead", "texto": "Casamento"},
        ],
    )

    assert res.texto_resposta == "Perfeito, seguimos com o casamento."


def test_tool_agendar_usa_nome_e_telefone_reais_do_contato():
    """
    Regressão do achado real em produção (2026-08-20): `agendar` gravava sempre
    cliente_nome="Lead ALFAIA" no ERP porque lia `ctx["lead"]` (que nunca teve campo `nome`/
    `telefone`) em vez de `ctx["contato"]` (onde esses dados realmente vivem).
    """
    contato = ContatoDTO(
        id="cnt_1", tenant_id="t1", nome="Valmir Moreira Junior",
        telefone="558591733321", primeiro_contato_em="2026-08-10",
    )
    lead = LeadModel(id="lead_1", tenant_id="t1", contato_id="cnt_1")

    resultado = tools_registry.executar_tool(
        "agendar",
        {"tipo": "prova", "data": "2026-08-21", "hora": "14:00"},
        {"tenant_id": "t1", "lead": lead, "contato": contato, "lead_service": None},
    )

    assert resultado["sucesso"] is True
    assert resultado["agendamento"]["cliente_nome"] == "Valmir Moreira Junior"
    assert resultado["agendamento"]["cliente_telefone"] == "558591733321"


def test_motor_nao_envia_midia_para_lista_com_multiplos_produtos():
    """
    Ajuste de produto (reversão, 2026-08-21): quando buscar_produtos retorna vários produtos
    (apresentação em lista), o motor NÃO monta midias_sugeridas — a lista é só texto, a foto só
    é enviada quando o lead escolhe um item específico (busca com 1 resultado só).
    """
    chamadas = {"n": 0}

    class FakeLLMComBuscaProdutos:
        def gerar_resposta(self, **kwargs):
            chamadas["n"] += 1
            if chamadas["n"] == 1:
                return LLMRespostaDTO(
                    content=None,
                    tool_calls=[LLMToolCallDTO(
                        id="call_1", nome="buscar_produtos",
                        argumentos={"evento": "casamento", "categoria": "noiva"},
                    )],
                )
            return LLMRespostaDTO(content="1. V-101 - Vestido Aurora - Champanhe - tamanhos: 36, 38, 40, 42")

    engine = AIEngineService(llm_client=FakeLLMComBuscaProdutos())
    contato = ContatoDTO(id="cnt_1", tenant_id="t1", telefone="5585988112233", primeiro_contato_em="2026-08-10")
    lead = LeadModel(id="lead_1", tenant_id="t1", contato_id="cnt_1")

    res = engine.processar_atendimento(
        tenant_id="t1",
        contato_dto=contato,
        lead_dto=lead,
        tipo_entrada="primeiro_contato",
        mensagens_inbound=["Quero um vestido para casamento"],
    )

    assert res.transbordo_acionado is False
    assert res.midias_sugeridas == []


def test_motor_envia_midia_com_codigo_em_formato_diferente_do_mock():
    """
    Achado de revisão (2026-08-21): o gate de mídia não pode depender do FORMATO do código
    (mock usa "T-203"; a WL real pode devolver outro formato, ex. só dígitos ou com underscore).
    O sinal real é `q` bater com o `ref` do único produto devolvido, seja qual for o formato.
    """
    produto_fake = {
        "nome": "Vestido Real", "ref": "10234", "cor": "Azul", "tamanho": "40",
        "valor_aluguel": 500.0, "imagem": "https://x/10234.jpg",
    }
    chamadas = {"n": 0}

    class FakeLLMComCodigoReal:
        def gerar_resposta(self, **kwargs):
            chamadas["n"] += 1
            if chamadas["n"] == 1:
                return LLMRespostaDTO(
                    content=None,
                    tool_calls=[LLMToolCallDTO(id="call_1", nome="buscar_produtos", argumentos={"q": "10234"})],
                )
            return LLMRespostaDTO(content="Esse é o Vestido Real. Gostou desse modelo?")

    engine = AIEngineService(llm_client=FakeLLMComCodigoReal())
    contato = ContatoDTO(id="cnt_1", tenant_id="t1", telefone="5585988112233", primeiro_contato_em="2026-08-10")
    lead = LeadModel(id="lead_1", tenant_id="t1", contato_id="cnt_1")

    import app.services.ai_engine as ai_engine_module
    original_executar_tool = ai_engine_module.tools_registry.executar_tool

    def fake_executar_tool(nome, argumentos, ctx):
        if nome == "buscar_produtos":
            return {"sucesso": True, "produtos": [produto_fake], "quantidade": 1}
        return original_executar_tool(nome, argumentos, ctx)

    ai_engine_module.tools_registry.executar_tool = fake_executar_tool
    try:
        res = engine.processar_atendimento(
            tenant_id="t1",
            contato_dto=contato,
            lead_dto=lead,
            tipo_entrada="primeiro_contato",
            mensagens_inbound=["Quero ver o 10234"],
        )
    finally:
        ai_engine_module.tools_registry.executar_tool = original_executar_tool

    assert len(res.midias_sugeridas) == 1
    assert res.midias_sugeridas[0].url == "https://x/10234.jpg"


def test_motor_acumula_midias_ao_selecionar_multiplos_itens():
    """
    Ajuste de seleção múltipla (2026-08-21): quando o lead escolhe mais de um item (ex.: "1,2"),
    a IA chama buscar_produtos uma vez por item no mesmo turno — as mídias acumulam entre essas
    chamadas (nunca "substitui", como antes), respeitando o teto de MAX_MIDIAS_POR_TROCA.
    """
    chamadas = {"n": 0}

    class FakeLLMComDoisItens:
        def gerar_resposta(self, **kwargs):
            chamadas["n"] += 1
            if chamadas["n"] == 1:
                return LLMRespostaDTO(
                    content=None,
                    tool_calls=[
                        LLMToolCallDTO(id="call_1", nome="buscar_produtos", argumentos={"q": "T-203"}),
                        LLMToolCallDTO(id="call_2", nome="buscar_produtos", argumentos={"q": "T-202"}),
                    ],
                )
            return LLMRespostaDTO(content="Aqui estão os dois. Gostou de algum?")

    engine = AIEngineService(llm_client=FakeLLMComDoisItens())
    contato = ContatoDTO(id="cnt_1", tenant_id="t1", telefone="5585988112233", primeiro_contato_em="2026-08-10")
    lead = LeadModel(id="lead_1", tenant_id="t1", contato_id="cnt_1")

    res = engine.processar_atendimento(
        tenant_id="t1",
        contato_dto=contato,
        lead_dto=lead,
        tipo_entrada="primeiro_contato",
        mensagens_inbound=["Quero ver o 1 e o 2"],
    )

    assert res.transbordo_acionado is False
    assert len(res.midias_sugeridas) == 2
    todas_legendas = " | ".join(m.legenda for m in res.midias_sugeridas)
    assert "T-203" in todas_legendas
    assert "T-202" in todas_legendas


def test_motor_marca_foto_nao_enviada_no_resultado_real_quando_atinge_o_teto():
    """
    Achado de revisão (2026-08-21): o teto de MAX_MIDIAS_POR_TROCA não pode truncar em silêncio —
    o resultado real da tool que o próprio modelo lê precisa dizer `foto_enviada: false` para a
    4ª seleção (além do teto de 3), senão o texto final pode afirmar que enviou uma foto que não
    foi enviada (mesma classe de bug do `caption` vs `text` do enviar_midia).
    """
    produtos_fake = {
        f"COD-{i}": {"nome": f"Terno {i}", "ref": f"COD-{i}", "cor": "Azul", "tamanho": "48", "imagem": f"https://x/{i}.jpg"}
        for i in range(1, 5)
    }
    chamadas = {"n": 0}
    mensagens_da_segunda_chamada = {}

    class FakeLLMComQuatroItens:
        def gerar_resposta(self, **kwargs):
            chamadas["n"] += 1
            if chamadas["n"] == 1:
                return LLMRespostaDTO(
                    content=None,
                    tool_calls=[
                        LLMToolCallDTO(id=f"call_{i}", nome="buscar_produtos", argumentos={"q": f"COD-{i}"})
                        for i in range(1, 5)
                    ],
                )
            mensagens_da_segunda_chamada.update({"mensagens": kwargs.get("mensagens")})
            return LLMRespostaDTO(content="Aqui estão os itens que consegui te mostrar agora.")

    engine = AIEngineService(llm_client=FakeLLMComQuatroItens())
    contato = ContatoDTO(id="cnt_1", tenant_id="t1", telefone="5585988112233", primeiro_contato_em="2026-08-10")
    lead = LeadModel(id="lead_1", tenant_id="t1", contato_id="cnt_1")

    import app.services.ai_engine as ai_engine_module
    original_executar_tool = ai_engine_module.tools_registry.executar_tool

    def fake_executar_tool(nome, argumentos, ctx):
        if nome == "buscar_produtos":
            produto = produtos_fake[argumentos["q"]]
            return {"sucesso": True, "produtos": [produto], "quantidade": 1}
        return original_executar_tool(nome, argumentos, ctx)

    ai_engine_module.tools_registry.executar_tool = fake_executar_tool
    try:
        res = engine.processar_atendimento(
            tenant_id="t1",
            contato_dto=contato,
            lead_dto=lead,
            tipo_entrada="primeiro_contato",
            mensagens_inbound=["Quero ver os 4 itens"],
        )
    finally:
        ai_engine_module.tools_registry.executar_tool = original_executar_tool

    assert len(res.midias_sugeridas) == 3

    resultados_tool = [
        json.loads(m["content"]) for m in mensagens_da_segunda_chamada["mensagens"] if m.get("role") == "tool"
    ]
    assert sum(1 for r in resultados_tool if r.get("foto_enviada") is True) == 3
    negados = [r for r in resultados_tool if r.get("foto_enviada") is False]
    assert len(negados) == 1
    assert "motivo_sem_foto" in negados[0]


def test_motor_nao_envia_midia_quando_filtro_afunila_para_um_produto_sem_codigo():
    """
    Achado de revisão (2026-08-21): uma busca de navegação comum (ex.: cor+tamanho juntos) pode
    afunilar para 1 resultado só, sem o lead ter apontado nenhum item específico da lista. Isso
    não é "escolha de item" — o motor só envia foto quando `q` em si é um código de peça.
    """
    chamadas = {"n": 0}

    class FakeLLMComFiltroEspecifico:
        def gerar_resposta(self, **kwargs):
            chamadas["n"] += 1
            if chamadas["n"] == 1:
                return LLMRespostaDTO(
                    content=None,
                    tool_calls=[LLMToolCallDTO(
                        id="call_1", nome="buscar_produtos",
                        argumentos={"categoria": "noiva", "cor": "Off-White", "tamanho": "36"},
                    )],
                )
            return LLMRespostaDTO(content="1. V-101 - Vestido Aurora - Off-White - tamanhos: 36")

    engine = AIEngineService(llm_client=FakeLLMComFiltroEspecifico())
    contato = ContatoDTO(id="cnt_1", tenant_id="t1", telefone="5585988112233", primeiro_contato_em="2026-08-10")
    lead = LeadModel(id="lead_1", tenant_id="t1", contato_id="cnt_1")

    res = engine.processar_atendimento(
        tenant_id="t1",
        contato_dto=contato,
        lead_dto=lead,
        tipo_entrada="primeiro_contato",
        mensagens_inbound=["Quero vestido de noiva off-white tamanho 36"],
    )

    assert res.midias_sugeridas == []


def test_motor_envia_midia_quando_lead_escolhe_item_unico_da_lista():
    """
    Ajuste de produto (reversão, 2026-08-21): quando o lead aponta um item específico e
    buscar_produtos retorna exatamente 1 produto, o motor monta a mídia real (foto) desse item.
    """
    chamadas = {"n": 0}

    class FakeLLMComItemUnico:
        def gerar_resposta(self, **kwargs):
            chamadas["n"] += 1
            if chamadas["n"] == 1:
                return LLMRespostaDTO(
                    content=None,
                    tool_calls=[LLMToolCallDTO(
                        id="call_1", nome="buscar_produtos", argumentos={"q": "V-101"},
                    )],
                )
            return LLMRespostaDTO(content="Esse é o Vestido Aurora. Gostou desse modelo?")

    engine = AIEngineService(llm_client=FakeLLMComItemUnico())
    contato = ContatoDTO(id="cnt_1", tenant_id="t1", telefone="5585988112233", primeiro_contato_em="2026-08-10")
    lead = LeadModel(id="lead_1", tenant_id="t1", contato_id="cnt_1")

    res = engine.processar_atendimento(
        tenant_id="t1",
        contato_dto=contato,
        lead_dto=lead,
        tipo_entrada="primeiro_contato",
        mensagens_inbound=["Quero ver o V-101"],
    )

    assert res.transbordo_acionado is False
    assert len(res.midias_sugeridas) == 1
    midia = res.midias_sugeridas[0]
    assert midia.url.startswith("https://")
    assert "Aurora" in midia.legenda
    assert "V-101" in midia.legenda


def test_motor_nao_sugere_midia_sem_buscar_produtos_na_troca():
    """Story 4.9, AC 7: sem chamada real a buscar_produtos nesta troca, nenhuma mídia é sugerida."""
    class FakeLLMSoTexto:
        def gerar_resposta(self, **kwargs):
            return LLMRespostaDTO(content="Claro, me conta mais sobre o evento.")

    engine = AIEngineService(llm_client=FakeLLMSoTexto())
    contato = ContatoDTO(id="cnt_1", tenant_id="t1", telefone="5585988112233", primeiro_contato_em="2026-08-10")
    lead = LeadModel(id="lead_1", tenant_id="t1", contato_id="cnt_1")

    res = engine.processar_atendimento(
        tenant_id="t1",
        contato_dto=contato,
        lead_dto=lead,
        tipo_entrada="primeiro_contato",
        mensagens_inbound=["Oi"],
    )

    assert res.midias_sugeridas == []


def test_motor_atualiza_nome_do_contato_via_nome_contato():
    """
    Regressão do achado real em produção (2026-08-21): agendamento sem forma confiável de contato
    além do telefone — a IA nunca tinha como corrigir o nome de exibição do WhatsApp (ex.:
    "valmirmoreirajunior"). `atualizar_lead` com `nome_contato` agora corrige `contato.nome` de
    verdade, e `processar_atendimento` reporta a mudança em `contato_nome_atualizado` para o
    chamador persistir.
    """
    class FakeLLMComNome:
        def gerar_resposta(self, **kwargs):
            return LLMRespostaDTO(
                content=None,
                tool_calls=[LLMToolCallDTO(
                    id="call_1", nome="atualizar_lead",
                    argumentos={"nome_contato": "Valmir Moreira Junior"},
                )],
            )

    engine = AIEngineService(llm_client=FakeLLMComNome())
    contato = ContatoDTO(
        id="cnt_1", tenant_id="t1", nome="valmirmoreirajunior",
        telefone="558591733321", primeiro_contato_em="2026-08-10",
    )
    lead = LeadModel(id="lead_1", tenant_id="t1", contato_id="cnt_1")

    res = engine.processar_atendimento(
        tenant_id="t1",
        contato_dto=contato,
        lead_dto=lead,
        tipo_entrada="continuacao",
        mensagens_inbound=["Meu nome completo é Valmir Moreira Junior"],
    )

    assert res.contato_nome_atualizado == "Valmir Moreira Junior"
    assert contato.nome == "Valmir Moreira Junior"


def test_agendar_com_cliente_telefone_nao_sobrescreve_telefone_de_envio():
    """
    Ajuste de agenda (2026-08-21): quem manda mensagem pode estar agendando para outra pessoa
    (ex.: esposa marcando prova para o esposo). `agendar.cliente_telefone` grava o telefone real
    de quem vai comparecer no registro do agendamento, mas `contato.telefone` — o endereço real de
    envio da resposta no WhatsApp — nunca é sobrescrito por esse dado (senão a confirmação iria
    para o número errado).
    """
    contato = ContatoDTO(
        id="cnt_1", tenant_id="t1", nome="Mariana Silva",
        telefone="5585988112233", primeiro_contato_em="2026-08-10",
    )
    lead = LeadModel(id="lead_1", tenant_id="t1", contato_id="cnt_1")
    ctx = {"tenant_id": "t1", "lead": lead, "contato": contato}

    resultado = tools_registry.executar_tool(
        "agendar",
        {
            "tipo": "prova", "data": "2026-09-05", "hora": "14:00",
            "cliente_telefone": "5585991234567",
        },
        ctx,
    )

    assert resultado["sucesso"] is True
    assert resultado["agendamento"]["cliente_telefone"] == "5585991234567"
    # O endereço de envio no WhatsApp continua o mesmo — nunca é trocado por dado de agendamento
    assert contato.telefone == "5585988112233"


def test_agendar_recusa_criar_agendamento_sem_nome_real():
    """
    Achado real em produção (2026-08-21): a IA confirmou o nome em texto ("Obrigado, Valmir
    Junior!") mas nunca chamou atualizar_lead, e o agendamento foi gravado com o nome de exibição
    genérico do WhatsApp mesmo assim. `agendar` agora recusa criar o agendamento (sem acionar
    transbordo — `sucesso: True`, `agendado: False`) quando não há nome real nem em
    `cliente_nome` nem já confirmado no contato.
    """
    contato = ContatoDTO(
        id="cnt_1", tenant_id="t1", nome="valmirmoreirajunior",
        telefone="5585988112233", primeiro_contato_em="2026-08-10",
    )
    lead = LeadModel(id="lead_501", tenant_id="t1", contato_id="cnt_1")
    ctx = {"tenant_id": "t1", "lead": lead, "contato": contato}

    resultado = tools_registry.executar_tool(
        "agendar",
        {"tipo": "prova", "data": "2026-09-06", "hora": "14:00"},
        ctx,
    )

    assert resultado["sucesso"] is True
    assert resultado["agendado"] is False
    assert resultado["motivo"] == "nome_pendente"
    assert "agendamento" not in resultado
    # Nome genérico do WhatsApp não é promovido a "nome real" por conta própria
    assert contato.nome == "valmirmoreirajunior"


def test_agendar_com_cliente_nome_direto_nao_depende_de_atualizar_lead_anterior():
    """
    `agendar.cliente_nome` grava o nome direto no agendamento mesmo que `atualizar_lead` nunca
    tenha sido chamado nesta conversa (achado real: a IA às vezes confirma o nome em texto mas
    pula a chamada de atualizar_lead) — e corrige `contato.nome` para os próximos turnos.
    """
    contato = ContatoDTO(
        id="cnt_1", tenant_id="t1", nome="valmirmoreirajunior",
        telefone="5585988112233", primeiro_contato_em="2026-08-10",
    )
    lead = LeadModel(id="lead_502", tenant_id="t1", contato_id="cnt_1")
    ctx = {"tenant_id": "t1", "lead": lead, "contato": contato}

    resultado = tools_registry.executar_tool(
        "agendar",
        {"tipo": "prova", "data": "2026-09-06", "hora": "14:00", "cliente_nome": "Valmir Junior"},
        ctx,
    )

    assert resultado["sucesso"] is True
    assert resultado["agendado"] is not False
    assert resultado["agendamento"]["cliente_nome"] == "Valmir Junior"
    assert contato.nome == "Valmir Junior"


def test_agendar_normaliza_telefone_sem_ddi():
    """
    Achado real em produção (2026-08-21): telefone de comparecimento gravado como
    "85991733321" (sem DDI 55), inconsistente com o formato usado no resto do sistema.
    `agendar.cliente_telefone` agora normaliza DDD+número para incluir o DDI.
    """
    contato = ContatoDTO(
        id="cnt_1", tenant_id="t1", nome="Mariana Silva",
        telefone="5585988112233", primeiro_contato_em="2026-08-10",
    )
    lead = LeadModel(id="lead_503", tenant_id="t1", contato_id="cnt_1")
    ctx = {"tenant_id": "t1", "lead": lead, "contato": contato}

    resultado = tools_registry.executar_tool(
        "agendar",
        {"tipo": "prova", "data": "2026-09-06", "hora": "14:00", "cliente_telefone": "85991733321"},
        ctx,
    )

    assert resultado["agendamento"]["cliente_telefone"] == "5585991733321"


def test_motor_nao_reporta_nome_atualizado_quando_nao_muda():
    class FakeLLMSemNome:
        def gerar_resposta(self, **kwargs):
            return LLMRespostaDTO(content="Perfeito, seguimos então.")

    engine = AIEngineService(llm_client=FakeLLMSemNome())
    contato = ContatoDTO(id="cnt_1", tenant_id="t1", nome="Mariana", telefone="5585988112233", primeiro_contato_em="2026-08-10")
    lead = LeadModel(id="lead_1", tenant_id="t1", contato_id="cnt_1")

    res = engine.processar_atendimento(
        tenant_id="t1",
        contato_dto=contato,
        lead_dto=lead,
        tipo_entrada="continuacao",
        mensagens_inbound=["Perfeito"],
    )

    assert res.contato_nome_atualizado is None
