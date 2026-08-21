import logging
from typing import Any, Literal
from pydantic import BaseModel, Field

logger = logging.getLogger("alfaia.tools_registry")


# Schemas Pydantic das 8 Tools de PRD §8.2

class BuscarProdutosInput(BaseModel):
    evento: str | None = Field(None, description="Tipo de evento (ex: casamento, formatura)")
    estilo: str | None = Field(None, description="Estilo da peça (ex: longo, curto, sereia)")
    categoria: str | None = Field(None, description="Categoria do vestuário")
    cor: str | None = Field(None, description="Cor de preferência")
    tamanho: str | None = Field(None, description="Tamanho da peça (ex: 38, 40, 42)")
    data_inicio: str | None = Field(None, description="Data início do evento YYYY-MM-DD")
    data_fim: str | None = Field(None, description="Data fim do evento YYYY-MM-DD")
    q: str | None = Field(None, description="Termo livre de busca")


class ConsultarSlotsInput(BaseModel):
    tipo: str = Field(..., description="Tipo de agendamento (ex: prova, retirada, ajuste)")
    # Opcional de propósito (ajuste de agenda, 2026-08-21): quando o lead ainda não tem um dia em
    # mente, chame sem `data_inicio` para receber os próximos dias reais com horário livre. Quando
    # o lead já propôs um dia, passe `data_inicio` — se esse dia não tiver vaga real, a tool devolve
    # os dias mais próximos que têm, nunca inventa nem escolhe uma data sozinha.
    data_inicio: str | None = Field(None, description="Data proposta pelo lead YYYY-MM-DD, se houver")
    data_fim: str | None = Field(None, description="Data fim YYYY-MM-DD")


class AgendarInput(BaseModel):
    tipo: str = Field(..., description="Tipo de agendamento (ex: prova, retirada, devolução)")
    data: str = Field(..., description="Data do agendamento YYYY-MM-DD")
    hora: str = Field(..., description="Horário do agendamento HH:MM")
    produto_ref: str | None = Field(None, description="Código ou referência da peça")
    observacao: str | None = Field(None, description="Observação adicional")
    # Nome completo de quem vai comparecer, passado diretamente aqui (não só via atualizar_lead)
    # para o agendamento nunca depender de uma chamada separada ter acontecido antes — achado real
    # em produção (2026-08-21): a IA confirmou o nome em texto ("Obrigado, Valmir Junior!") mas
    # nunca chamou atualizar_lead, e o agendamento foi gravado com o nome de exibição genérico do
    # WhatsApp mesmo assim. Se omitido, usa o nome já confirmado no contato (se houver).
    cliente_nome: str | None = Field(
        None, description="Nome completo de quem vai comparecer, confirmado nesta conversa"
    )
    # Telefone de quem vai efetivamente comparecer ao agendamento, quando for diferente do número
    # de WhatsApp que está enviando a mensagem (ex.: esposa agendando prova para o esposo, mãe
    # para filho/filha) — só preencher se o lead informar explicitamente. NUNCA usar este campo
    # para trocar o número de WhatsApp que recebe a resposta (isso é `contato.telefone`, é o
    # endereço de envio real e não pode ser sobrescrito por um dado de agendamento).
    cliente_telefone: str | None = Field(
        None, description="Telefone de quem vai comparecer ao agendamento, se diferente de quem está conversando"
    )


class AtualizarLeadInput(BaseModel):
    evento_tipo: str | None = None
    evento_data: str | None = None
    papel: str | None = None
    peca_interesse: str | None = None
    tamanho: str | None = None
    cor: str | None = None
    valor_estimado: float | None = None
    # Nome real do lead, informado/confirmado por ele na conversa — nunca o nome de exibição do
    # WhatsApp (achado real em produção, 2026-08-21: agendamento sem forma confiável de contato
    # além do telefone). Vive em ContatoDTO, não em LeadDTO — tratado à parte no tool handler.
    nome_contato: str | None = None


class MoverStatusInput(BaseModel):
    status_destino: str = Field(..., description="Status destino no Kanban (ex: qualificando, orcamento, negociando, descartado)")
    motivo: str | None = Field(None, description="Motivo textual da movimentação (obrigatório para descarte)")


class RegistrarInteresseInput(BaseModel):
    evento_tipo: str | None = None
    evento_data: str | None = None
    papel: str | None = None
    peca_interesse: str | None = None
    tamanho: str | None = None
    cor: str | None = None
    valor_estimado: float | None = None


class AbrirTransbordoInput(BaseModel):
    motivo: str = Field(..., description="Motivo do transbordo humano (ex: solicitação explícita, assunto crítico, erro de API)")
    criticidade: Literal["baixa", "media", "alta"] = Field("media", description="Nível de criticidade do transbordo")


class EncerrarInput(BaseModel):
    desfecho: Literal["ganho", "descartado"] = Field(..., description="Desfecho do atendimento (ganho ou descartado)")
    motivo: str | None = Field(None, description="Motivo textual do encerramento")


# Descrição de nível de função (não de campo) para cada tool — texto que o LLM lê para
# decidir QUANDO chamar, na mesma linha do efeito documentado em PRD §8.2 e Dev Notes da story 4.3.
TOOL_DESCRIPTIONS: dict[str, str] = {
    "buscar_produtos": (
        "Busca peças reais no catálogo da WebLocação por evento, estilo, categoria, cor, tamanho "
        "e período — nunca inventar produto, disponibilidade ou preço sem o resultado desta tool.\n"
        "FLUXO OBRIGATÓRIO (lista em texto primeiro, foto só sob pedido):\n"
        "1) Quando o lead disser pela primeira vez qual tipo de peça/traje quer, ou pedir para ver "
        "mais opções, chame esta tool sem código específico e apresente TODOS os produtos "
        "retornados como uma LISTA NUMERADA em texto, uma linha por produto, exatamente neste "
        "formato: 'N - cód. <código> - <descrição/nome> — <cor> — tamanhos <tamanhos disponíveis, "
        "separados por vírgula>' (ex.: '1 - cód. T-203 - Terno Linho Praia Champanhe — Bege Claro "
        "— tamanhos 46, 48, 50'). NUNCA inclua o valor de aluguel nessa lista — só informe o preço "
        "se o lead perguntar explicitamente (e mesmo assim consulte o dado real da tool, nunca "
        "invente). Nenhuma foto é enviada nesta etapa; o sistema só envia foto quando o lead "
        "escolhe item(ns) específico(s) (passo 2). Termine SEMPRE a lista com esta pergunta: "
        "'Quer ver a imagem de qual dos itens acima? Digite o número do item ou o código. Se "
        "quiser ver mais de um, separe por vírgula (ex.: 1,2) ou digite \"todos\".'\n"
        "2) Quando o lead responder com um ou mais números (ex.: '1,2' ou 'quero ver o 3'), "
        "código(s) (ex.: 'T-203'), 'todos', ou uma característica que aponte para item(ns) "
        "específico(s) da lista que VOCÊ MESMA mostrou nesta conversa, volte na sua própria lista "
        "anterior, identifique o(s) código(s) correspondente(s) e chame esta tool UMA VEZ PARA "
        "CADA item escolhido, passando o código dele em `q` (uma tool call por item, todas no "
        "mesmo turno) — cada chamada com 1 código retorna 1 produto e o sistema envia a foto dele "
        "automaticamente, na ordem em que você chamou. O sistema envia no máximo 3 fotos por troca "
        "— o resultado de CADA chamada traz `foto_enviada` (true/false); se vier `false` (com "
        "`motivo_sem_foto` explicando, ex.: limite de fotos atingido), a foto REALMENTE não foi "
        "enviada — nunca diga ao lead que mandou uma foto que o resultado marcou como não enviada; "
        "diga que pode mandar o restante depois se ele quiser. Seu texto depois das fotos deve ser "
        "curto, sem repetir os dados já mostrados nas legendas, e sempre terminar oferecendo: 'Se "
        "quiser ver mais itens, é só me dizer o número, o código ou alguma característica.'\n"
        "3) Só avance para a etapa de agendamento depois que o lead CONFIRMAR de forma clara que "
        "gostou de um item específico (ex.: 'sim, gostei desse', 'é esse mesmo', 'pode ser esse'). "
        "Ao confirmar, repita de volta qual item ele escolheu (código e nome). Se ele não "
        "confirmar, pedir para ver outro item, ou hesitar, mostre a lista novamente (ou busque o(s) "
        "item(ns) pedido(s)) — nunca avance para agendamento sem essa confirmação explícita.\n"
        "NUNCA diga que está 'enviando imagem' (quem envia é o sistema) nem escreva a URL da "
        "imagem ou sintaxe de link/imagem (como ![]() ou [texto](url)) na resposta — o lead recebe "
        "a foto direto no WhatsApp, a URL no texto só vira link quebrado."
    ),
    "consultar_slots": (
        "Consulta a agenda REAL para agendamento (prova, retirada, ajuste) — nunca inventar "
        "disponibilidade. FLUXO OBRIGATÓRIO:\n"
        "1) Assim que o lead confirmar o item e topar agendar, e ele ainda não tiver dito um dia de "
        "preferência, chame esta tool SEM `data_inicio` — ela devolve os próximos dias reais com "
        "horário livre (campo `dias_disponiveis`, cada um com sua lista de horários). Apresente "
        "isso ao lead numa frase natural e curta (ex.: 'Tenho vaga terça (25/08) às 9h ou 14h, e "
        "quarta (26/08) às 10h — algum desses funciona? Ou me diga o dia e horário que prefere que "
        "eu vejo se tem vaga'). NUNCA em lista com bullet/número/quebra de linha por dia — uma "
        "lista quebrada em linhas sem o formato de catálogo de produto é removida pela sanitização "
        "de menu do sistema antes de chegar ao lead.\n"
        "2) Se o lead já disser um dia/horário de preferência (seja na primeira mensagem sobre "
        "agendamento ou respondendo à sua oferta), chame esta tool COM `data_inicio` nesse dia. Se "
        "`data_pedida_disponivel` vier `true`, confirme esse horário com o lead. Se vier `false`, o "
        "dia pedido não tem vaga real (fechado ou lotado) — nunca insista nele nem invente um "
        "horário parecido: diga isso com naturalidade e ofereça o dia mais próximo real que "
        "aparece em `dias_disponiveis` (ex.: 'Nesse dia não tenho vaga, mas na quinta 27/08 tenho "
        "às 11h — funciona?').\n"
        "3) Só chame `agendar` depois que o lead confirmar um horário que veio de um resultado "
        "REAL desta tool nesta mesma conversa — nunca por conta própria."
    ),
    "agendar": (
        "Cria de fato um agendamento na WebLocação para o lead atual. Só chamar depois que (a) o "
        "lead confirmou um horário retornado por consultar_slots nesta mesma conversa, e (b) você "
        "já tem, nesta conversa, o NOME COMPLETO e o TELEFONE de quem vai efetivamente comparecer — "
        "pergunte sempre nessa ordem, um dado por mensagem: primeiro o nome completo, depois o "
        "telefone. Isso é obrigatório mesmo quando o lead já demonstrou interesse claro, porque "
        "quem está mandando mensagem pode estar agendando para outra pessoa (ex.: esposa marcando "
        "prova para o esposo, mãe para filho ou filha) — nunca assuma que o nome de exibição do "
        "WhatsApp (ex.: 'valmirmoreirajunior') ou o número que está conversando são os dados reais "
        "de quem vai à prova. Passe o nome confirmado direto no parâmetro `cliente_nome` desta "
        "própria tool (não basta ter dito o nome antes numa outra mensagem — mande aqui também), e "
        "o telefone de quem vai comparecer (se diferente de quem está conversando) em "
        "`cliente_telefone` — nunca troque o número que está recebendo esta conversa. O resultado "
        "desta tool pode vir com `agendado: false`: se `motivo` for `nome_pendente`, use exatamente "
        "a `mensagem` devolvida para pedir de novo (ela já diz se falta o nome inteiro ou só o "
        "sobrenome — nunca repita a mesma pergunta genérica se o lead já tinha respondido algo, "
        "senão a conversa trava em loop); se for `horario_indisponivel`, "
        "o horário deixou de estar livre entre a consulta e agora — nunca diga que confirmou, "
        "ofereça o dia/horário real sugerido em `dias_disponiveis` e tente `agendar` de novo só "
        "depois que o lead confirmar. Sempre passe `produto_ref` quando o agendamento for para "
        "experimentar/retirar uma peça específica já identificada na conversa. Na mensagem final de "
        "confirmação (só quando `agendado` vier `true`), informe a data completa com dia, mês e ANO "
        "no formato dd/mm/aaaa (ex.: '22/08/2026', nunca '2026-08-22' nem só '22/08') — é a única "
        "garantia real que o lead tem de que a data e o ano estão certos."
    ),
    "atualizar_lead": (
        "Atualiza os dados de interesse do lead atual (evento, peça, tamanho, cor, valor estimado) "
        "coletados na conversa até agora. Use `nome_contato` quando o lead informar ou confirmar o "
        "nome completo, para a IA passar a chamá-lo pelo nome no restante da conversa — mas isso "
        "NÃO substitui passar `cliente_nome` na hora de chamar `agendar`, que exige o nome de novo "
        "naquele momento (garantia independente, ver instrução da tool `agendar`). O telefone de "
        "quem vai comparecer ao agendamento NÃO é atualizado por aqui — vai direto em "
        "`agendar.cliente_telefone` na hora de confirmar o agendamento."
    ),
    "mover_status": (
        "Move o lead para outro status no Kanban conforme a evolução da conversa (ex.: qualificando, "
        "orcamento, negociando, descartado). Nunca mover para 'ganho' — isso é exclusivo de humano."
    ),
    "registrar_interesse": "Registra um snapshot do interesse atual do lead para histórico.",
    "abrir_transbordo": (
        "Aciona atendimento humano quando a IA não consegue resolver, há erro de sistema/API, "
        "ou o lead pede explicitamente para falar com uma pessoa."
    ),
    "encerrar": (
        "Encerra o atendimento como descartado. Nunca chamar com desfecho 'ganho' — fechamento de "
        "contrato é sempre decisão humana (MV1)."
    ),
}


class ToolsRegistry:
    """
    Registro Central e Execuror das 8 Ferramentas do Motor de IA (PRD §8.2, AC 5).
    """

    def __init__(self):
        self.ferramentas = {
            "buscar_produtos": self.buscar_produtos,
            "consultar_slots": self.consultar_slots,
            "agendar": self.agendar,
            "atualizar_lead": self.atualizar_lead,
            "mover_status": self.mover_status,
            "registrar_interesse": self.registrar_interesse,
            "abrir_transbordo": self.abrir_transbordo,
            "encerrar": self.encerrar,
        }
        self._modelos_entrada: dict[str, type[BaseModel]] = {
            "buscar_produtos": BuscarProdutosInput,
            "consultar_slots": ConsultarSlotsInput,
            "agendar": AgendarInput,
            "atualizar_lead": AtualizarLeadInput,
            "mover_status": MoverStatusInput,
            "registrar_interesse": RegistrarInteresseInput,
            "abrir_transbordo": AbrirTransbordoInput,
            "encerrar": EncerrarInput,
        }

    def function_schemas(self) -> list[dict[str, Any]]:
        """
        Gera os schemas de function-calling (formato OpenAI/OpenRouter) das 8 tools, a partir dos
        mesmos modelos Pydantic usados para validar a execução — uma única fonte de verdade para
        o que a IA pode chamar e para o que `executar_tool` de fato aceita (story 4.8, AC 1).
        """
        schemas = []
        for nome, modelo in self._modelos_entrada.items():
            parametros = modelo.model_json_schema()
            parametros.pop("title", None)
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": nome,
                        "description": TOOL_DESCRIPTIONS[nome],
                        "parameters": parametros,
                    },
                }
            )
        return schemas

    def executar_tool(self, nome_tool: str, argumentos: dict[str, Any], contexto_execucao: dict[str, Any]) -> dict[str, Any]:
        if nome_tool not in self.ferramentas:
            logger.error(f"Tool desconhecida tentada pela IA: '{nome_tool}'")
            return {"sucesso": False, "erro": f"Ferramenta '{nome_tool}' não registrada."}

        func = self.ferramentas[nome_tool]
        try:
            return func(argumentos, contexto_execucao)
        except Exception as e:
            logger.error(f"Falha na execução da tool '{nome_tool}': {e}")
            return {"sucesso": False, "erro": str(e), "acao": "abrir_transbordo"}

    def buscar_produtos(self, args: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        params = BuscarProdutosInput(**args)
        tenant_id = ctx.get("tenant_id", "tenant_piloto")
        logger.info(f"Tool 'buscar_produtos' executada [params={params.model_dump(exclude_none=True)}]")

        from app.services.product_search_service import product_search_service
        return product_search_service.buscar_produtos_com_cache(
            tenant_id=tenant_id,
            params=params.model_dump(exclude_none=True),
        )

    def consultar_slots(self, args: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        params = ConsultarSlotsInput(**args)
        tenant_id = ctx.get("tenant_id", "tenant_piloto")
        logger.info(f"Tool 'consultar_slots' executada [params={params.model_dump()}]")

        from app.services.scheduling_service import scheduling_service
        return scheduling_service.consultar_slots(
            tenant_id=tenant_id,
            tipo=params.tipo,
            data_inicio=params.data_inicio,
            data_fim=params.data_fim,
        )

    # Mesmos termos genéricos tratados em `webhooks.py::_nome_generico` — duplicado aqui de
    # propósito (import de `webhooks.py` para dentro de `tools_registry.py` criaria dependência
    # invertida do router para o service) para o gate de `agendar` não depender de nenhum outro
    # passo ter rodado antes (achado real em produção, 2026-08-21).
    _NOME_GENERICO_TERMOS = {"", "cliente", "cliente whatsapp", "whatsapp", "sem nome", "lead alfaia"}

    @classmethod
    def _nome_ainda_generico(cls, nome: str | None) -> bool:
        normalizado = " ".join(str(nome or "").strip().split())
        if not normalizado or normalizado.lower() in cls._NOME_GENERICO_TERMOS:
            return True
        # Exige "nome completo" (pelo menos duas palavras) — um nome de exibição de WhatsApp numa
        # palavra só (ex.: "valmirmoreirajunior") passa pelo filtro mais permissivo usado em outros
        # pontos do sistema (ele não é um dos termos-placeholder acima), mas não é um nome real
        # confirmado pelo lead. Achado real em produção (2026-08-21): esse valor exato chegou a ser
        # gravado como `cliente_nome` no agendamento — este gate é mais rígido de propósito.
        return " " not in normalizado

    @staticmethod
    def _normalizar_telefone_br(telefone: str | None) -> str | None:
        """Garante o DDI 55 quando o lead digita só DDD+número (achado real em produção,
        2026-08-21: telefone de comparecimento gravado como "85991733321", sem DDI, inconsistente
        com o formato usado em todo o resto do sistema). Não valida DDD/tamanho — só evita o caso
        mais comum de dado incompleto; nunca inventa dígitos que o lead não informou."""
        if not telefone:
            return telefone
        digitos = "".join(c for c in telefone if c.isdigit())
        if len(digitos) in (10, 11) and not digitos.startswith("55"):
            digitos = "55" + digitos
        return digitos or telefone

    def agendar(self, args: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        params = AgendarInput(**args)
        tenant_id = ctx.get("tenant_id", "tenant_piloto")
        lead = ctx.get("lead")
        contato = ctx.get("contato")
        lead_id = lead.id if lead else "lead_piloto"

        # Garantia dura de nome (achado real em produção, 2026-08-21): a IA confirmou o nome em
        # texto mas nunca chamou atualizar_lead, e o agendamento foi gravado com o nome de exibição
        # genérico do WhatsApp mesmo assim. `agendar` agora aceita `cliente_nome` diretamente (não
        # depende de uma chamada separada anterior) e, se ainda assim não houver nome real nem aqui
        # nem já confirmado no contato, RECUSA criar o agendamento — nunca grava um nome genérico
        # no ERP. `sucesso: True`/`agendado: False` (não é falha de sistema, não aciona transbordo)
        # para a IA simplesmente pedir o nome de novo.
        cliente_nome = params.cliente_nome or (contato.nome if contato and getattr(contato, "nome", None) else None)
        if self._nome_ainda_generico(cliente_nome):
            # Mensagem diferente quando já veio ALGUMA coisa (só falta o sobrenome) vs. nada ainda
            # — sem isso, um lead que já respondeu com um único nome ("Valmir") recebe de volta a
            # mesma pergunta genérica e pode ficar em loop sem entender o que falta (achado de
            # revisão, 2026-08-21).
            nome_bruto = " ".join(str(cliente_nome or "").strip().split())
            if nome_bruto and nome_bruto.lower() not in self._NOME_GENERICO_TERMOS:
                mensagem = f'Preciso também do sobrenome — "{nome_bruto}" sozinho não é suficiente para o agendamento.'
            else:
                mensagem = "Ainda não tenho o nome completo (nome e sobrenome) de quem vai comparecer — preciso dele antes de confirmar o agendamento."
            return {
                "sucesso": True,
                "agendado": False,
                "motivo": "nome_pendente",
                "mensagem": mensagem,
            }
        # Corrige o nome do contato para os próximos turnos (ex.: a IA passar a chamar o lead pelo
        # nome) sempre que `agendar` já recebeu um nome real direto — não depende de atualizar_lead.
        if contato and params.cliente_nome and not self._nome_ainda_generico(params.cliente_nome):
            contato.nome = params.cliente_nome

        # `params.cliente_telefone` é o telefone de quem vai comparecer, quando informado
        # explicitamente e diferente de quem está conversando — só usado para o registro do
        # agendamento, NUNCA sobrescreve `contato.telefone` (endereço real de envio da resposta
        # no WhatsApp; achado real, 2026-08-21: confundir os dois faria a confirmação ir para o
        # número errado quando alguém agenda para outra pessoa).
        cliente_telefone = self._normalizar_telefone_br(params.cliente_telefone) or (
            contato.telefone if contato and getattr(contato, "telefone", None) else "5585988112233"
        )

        logger.info(f"Tool 'agendar' executada [params={params.model_dump()}]")

        from app.services.scheduling_service import scheduling_service
        return scheduling_service.agendar_prova_ou_retirada(
            tenant_id=tenant_id,
            lead_id=lead_id,
            tipo=params.tipo,
            data=params.data,
            hora=params.hora,
            cliente_nome=cliente_nome,
            cliente_telefone=cliente_telefone,
            produto_ref=params.produto_ref,
            observacao=params.observacao,
        )

    def atualizar_lead(self, args: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        params = AtualizarLeadInput(**args)
        dados = params.model_dump(exclude_none=True)
        # nome_contato vive em ContatoDTO, não em LeadDTO/LeadModel (que nunca tiveram esse
        # campo — mesmo motivo do bug real corrigido na story 5.3). O telefone de quem vai
        # comparecer ao agendamento NÃO passa por aqui — vai direto em `agendar.cliente_telefone`,
        # nunca sobrescrevendo `contato.telefone` (endereço real de envio no WhatsApp).
        nome_contato = dados.pop("nome_contato", None)

        lead = ctx.get("lead")
        if lead:
            for k, v in dados.items():
                setattr(lead, k, v)

        if nome_contato:
            contato = ctx.get("contato")
            if contato:
                contato.nome = nome_contato

        logger.info(f"Tool 'atualizar_lead' executada [params={params.model_dump(exclude_none=True)}]")
        return {"sucesso": True, "mensagem": "Dados do lead atualizados."}

    def mover_status(self, args: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        params = MoverStatusInput(**args)
        from app.services.status_transition_service import status_transition_service
        lead = ctx.get("lead")
        tenant_id = ctx.get("tenant_id", "tenant_piloto")
        lead_service = ctx.get("lead_service")

        if not lead:
            return {"sucesso": False, "erro": "Objeto lead ausente no contexto."}

        sucesso, msg = status_transition_service.validar_e_mover_status(
            tenant_id=tenant_id,
            lead=lead,
            status_destino=params.status_destino,
            autor="ia",
            motivo=params.motivo,
            lead_service=lead_service,
        )

        return {"sucesso": sucesso, "mensagem": msg}

    def registrar_interesse(self, args: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        params = RegistrarInteresseInput(**args)
        from app.services.interest_service import interest_service
        lead = ctx.get("lead")
        tenant_id = ctx.get("tenant_id", "tenant_piloto")
        lead_service = ctx.get("lead_service")

        if not lead or not lead_service:
            return {"sucesso": False, "erro": "Objeto lead/service ausente no contexto."}

        lead_resultante, registro, tipo = interest_service.processar_registro_interesse(
            tenant_id=tenant_id,
            lead_atual=lead,
            lead_service=lead_service,
            novo_interesse=params.model_dump(exclude_none=True),
        )

        return {
            "sucesso": True,
            "tipo_mudanca": tipo,
            "versao_interesse": registro.versao if registro else 1,
            "novo_lead_id": lead_resultante.id,
        }

    def abrir_transbordo(self, args: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        params = AbrirTransbordoInput(**args)
        conversa = ctx.get("conversa")
        if conversa:
            conversa["estado"] = "transbordo"
        logger.info(f"Tool 'abrir_transbordo' acionada [motivo={params.motivo}]")
        return {"sucesso": True, "estado": "transbordo", "mensagem": "Transbordo humano acionado."}

    def encerrar(self, args: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        params = EncerrarInput(**args)
        if params.desfecho == "ganho":
            return {"sucesso": False, "erro": "MV1: A IA não pode encerrar como ganho. Apenas operador humano fecha contrato."}

        return self.mover_status({"status_destino": "descartado", "motivo": params.motivo or "Encerramento via IA"}, ctx)


tools_registry = ToolsRegistry()
