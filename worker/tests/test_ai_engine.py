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
        {"tipo": "prova", "data": "2026-08-21", "hora": "08:00"},
        {"tenant_id": "t1", "lead": lead, "contato": contato, "lead_service": None},
    )

    assert resultado["sucesso"] is True
    assert resultado["agendamento"]["cliente_nome"] == "Valmir Moreira Junior"
    assert resultado["agendamento"]["cliente_telefone"] == "558591733321"


def test_motor_monta_midias_reais_apos_buscar_produtos_com_sucesso():
    """
    Story 4.9, AC 1, 2, 6: quando buscar_produtos retorna produtos reais com imagem, o motor
    monta midias_sugeridas com url/legenda vindos do resultado real da tool (nome, cor, tamanho,
    valor) — nunca inventados.
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
            return LLMRespostaDTO(content="Temos duas opções lindas para o seu casamento.")

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
    assert len(res.midias_sugeridas) == 2
    primeira = res.midias_sugeridas[0]
    assert primeira.url.startswith("https://")
    assert "Aurora" in primeira.legenda
    assert "V-101" in primeira.legenda
    assert "36, 38, 40, 42" in primeira.legenda
    assert "890" in primeira.legenda


def test_motor_respeita_limite_de_midias_por_troca():
    """Story 4.9, AC 1: no máximo MAX_MIDIAS_POR_TROCA imagens, mesmo com mais produtos retornados."""
    produtos_fake = [
        {"nome": f"Terno {i}", "cor": "Azul", "tamanho": "48", "valor_aluguel": 400.0, "imagem": f"https://x/{i}.jpg"}
        for i in range(5)
    ]

    chamadas = {"n": 0}

    class FakeLLMComMuitosProdutos:
        def gerar_resposta(self, **kwargs):
            chamadas["n"] += 1
            if chamadas["n"] == 1:
                return LLMRespostaDTO(
                    content=None,
                    tool_calls=[LLMToolCallDTO(id="call_1", nome="buscar_produtos", argumentos={"evento": "casamento"})],
                )
            return LLMRespostaDTO(content="Temos várias opções para o seu casamento.")

    engine = AIEngineService(llm_client=FakeLLMComMuitosProdutos())
    contato = ContatoDTO(id="cnt_1", tenant_id="t1", telefone="5585988112233", primeiro_contato_em="2026-08-10")
    lead = LeadModel(id="lead_1", tenant_id="t1", contato_id="cnt_1")

    import app.services.ai_engine as ai_engine_module

    original_executar_tool = ai_engine_module.tools_registry.executar_tool

    def fake_executar_tool(nome, argumentos, ctx):
        if nome == "buscar_produtos":
            return {"sucesso": True, "produtos": produtos_fake, "quantidade": len(produtos_fake)}
        return original_executar_tool(nome, argumentos, ctx)

    ai_engine_module.tools_registry.executar_tool = fake_executar_tool
    try:
        res = engine.processar_atendimento(
            tenant_id="t1",
            contato_dto=contato,
            lead_dto=lead,
            tipo_entrada="primeiro_contato",
            mensagens_inbound=["Quero ver ternos para casamento"],
        )
    finally:
        ai_engine_module.tools_registry.executar_tool = original_executar_tool

    assert len(res.midias_sugeridas) == AIEngineService.MAX_MIDIAS_POR_TROCA


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
