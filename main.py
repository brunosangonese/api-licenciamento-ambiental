
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional
import math
import re

app = FastAPI(
    title="Sistema de Licenciamento Ambiental",
    description="Protótipo de enquadramento ambiental",
    version="0.4.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

ATIVIDADES = [
    {
        "id": 1,
        "codram": "DEMO-001",
        "descricao": "Atividade com enquadramento por área",
        "parametro": "Área útil",
        "unidade": "m²",
        "potencial_poluidor": "Médio",
        "ativo": True
    },
    {
        "id": 2,
        "codram": "112,12",
        "descricao": "Criação de aves de postura",
        "parametro": "Número de cabeças",
        "unidade": "un",
        "potencial_poluidor": "Médio",
        "ativo": True
    }
]


class DadosEnquadramento(BaseModel):
    codram_id: int
    quantidade: Optional[int] = Field(default=None, gt=0)
    area_util: Optional[float] = Field(default=None, gt=0)


def interpretar_busca(search):
    if not search:
        return []

    termos = []

    for parte in search.split(";"):
        parte = parte.strip()

        if not parte:
            continue

        resultado = re.match(
            r'^\s*(codram|descricao)\s*=\s*acc\s*=\s*"(.*?)"\s*$',
            parte,
            re.IGNORECASE
        )

        if resultado:
            campo = resultado.group(1).lower()
            valor = resultado.group(2).strip("*").lower()

            if valor:
                termos.append((campo, valor))
        else:
            termos.append(("geral", parte.lower().strip("*")))

    return termos


def enquadrar_aves(quantidade):
    if quantidade <= 1000:
        return {
            "porte": "Isento",
            "faixa_porte": "Até 1.000 cabeças",
            "competencia": "Isento de licenciamento",
            "situacao": "Atividade isenta de licenciamento."
        }

    elif quantidade <= 40000:
        return {
            "porte": "Mínimo",
            "faixa_porte": "De 1.001 até 40.000 cabeças",
            "competencia": "Municipal",
            "indice_taxa": 1,
            "situacao": "Licenciamento de competência municipal."
        }

    elif quantidade <= 80000:
        return {
            "porte": "Pequeno",
            "faixa_porte": "De 40.001 até 80.000 cabeças",
            "competencia": "Municipal",
            "indice_taxa": 2,
            "situacao": "Licenciamento de competência municipal."
        }

    elif quantidade <= 120000:
        return {
            "porte": "Médio",
            "faixa_porte": "De 80.001 até 120.000 cabeças",
            "competencia": "Municipal",
            "indice_taxa": 3,
            "situacao": "Licenciamento de competência municipal."
        }

    elif quantidade <= 160000:
        return {
            "porte": "Grande",
            "faixa_porte": "De 120.001 até 160.000 cabeças",
            "competencia": "Estadual",
            "situacao": (
                "Licenciamento de competência do órgão "
                "ambiental estadual."
            )
        }

    else:
        return {
            "porte": "Excepcional",
            "faixa_porte": "Acima de 160.000 cabeças",
            "competencia": "Estadual",
            "situacao": (
                "Licenciamento de competência do órgão "
                "ambiental estadual."
            )
        }


@app.get("/", response_class=HTMLResponse)
def pagina_inicial():
    return HTML


@app.get("/api/health")
def health():
    return {
        "sistema": "Licenciamento Ambiental",
        "status": "online",
        "versao": "0.4.0"
    }


@app.get("/api/licenciamento/codrams")
def listar_codrams(
    page: int = Query(default=0, ge=0),
    size: int = Query(default=10, ge=1, le=100),
    search: str = ""
):
    resultados = [
        item for item in ATIVIDADES if item["ativo"]
    ]

    for campo, valor in interpretar_busca(search):
        if campo == "codram":
            resultados = [
                item for item in resultados
                if valor in item["codram"].lower()
            ]

        elif campo == "descricao":
            resultados = [
                item for item in resultados
                if valor in item["descricao"].lower()
            ]

        else:
            resultados = [
                item for item in resultados
                if valor in (
                    item["codram"] + " " + item["descricao"]
                ).lower()
            ]

    total = len(resultados)
    inicio = page * size
    fim = inicio + size

    return {
        "content": resultados[inicio:fim],
        "page": page,
        "size": size,
        "totalElements": total,
        "totalPages": math.ceil(total / size) if total else 0
    }


@app.post("/api/licenciamento/enquadrar")
def enquadrar(dados: DadosEnquadramento):
    atividade = next(
        (
            item for item in ATIVIDADES
            if item["id"] == dados.codram_id
        ),
        None
    )

    if not atividade:
        raise HTTPException(
            status_code=404,
            detail="Atividade não encontrada."
        )

    if dados.codram_id == 2:
        if dados.quantidade is None:
            raise HTTPException(
                status_code=400,
                detail="Informe o número de cabeças."
            )

        resultado = enquadrar_aves(dados.quantidade)

        return {
            "atividade": atividade["descricao"],
            "codram": atividade["codram"],
            "quantidade": dados.quantidade,
            "unidade": "un",
            "potencial_poluidor": atividade["potencial_poluidor"],
            **resultado
        }

    if dados.codram_id == 1:
        if dados.area_util is None:
            raise HTTPException(
                status_code=400,
                detail="Informe a área útil."
            )

        area = dados.area_util

        if area <= 1000:
            porte = "Pequeno"
            faixa = "Até 1.000 m²"
        elif area <= 5000:
            porte = "Médio"
            faixa = "Acima de 1.000 até 5.000 m²"
        else:
            porte = "Grande"
            faixa = "Acima de 5.000 m²"

        return {
            "atividade": atividade["descricao"],
            "codram": atividade["codram"],
            "area_util": area,
            "unidade": "m²",
            "porte": porte,
            "faixa_porte": faixa,
            "potencial_poluidor": "Médio",
            "competencia": "Municipal",
            "situacao": "Enquadramento demonstrativo."
        }

    raise HTTPException(
        status_code=400,
        detail="Atividade sem regra de enquadramento cadastrada."
    )


HTML = r"""
<!DOCTYPE html>
<html lang="pt-BR">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>Licenciamento Ambiental</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            background: #f3f5f4;
            color: #26352e;
            font-family: Arial, sans-serif;
        }

        header {
            background: #24543e;
            color: white;
            padding: 28px 20px;
        }

        header h1 {
            max-width: 760px;
            margin: auto;
            font-size: 23px;
            font-weight: 600;
        }

        header p {
            max-width: 760px;
            margin: 8px auto 0;
            color: #dce9e0;
            font-size: 14px;
        }

        main {
            max-width: 760px;
            margin: 35px auto;
            padding: 0 16px;
        }

        .card {
            background: white;
            border: 1px solid #e0e6e2;
            border-radius: 10px;
            padding: 26px;
            box-shadow: 0 3px 12px rgba(0,0,0,0.04);
        }

        h2 {
            margin: 0 0 8px;
            font-size: 21px;
        }

        .subtitulo {
            color: #6b7770;
            font-size: 14px;
            margin-bottom: 25px;
            line-height: 1.5;
        }

        label {
            display: block;
            font-size: 14px;
            font-weight: 600;
            margin: 18px 0 8px;
        }

        input, select {
            width: 100%;
            padding: 13px;
            border: 1px solid #cbd5ce;
            border-radius: 6px;
            background: white;
            font-size: 15px;
            color: #26352e;
        }

        input:focus, select:focus {
            outline: 2px solid #8bb59c;
            border-color: #397c56;
        }

        .ajuda {
            margin-top: 7px;
            color: #77837b;
            font-size: 12px;
        }

        #campoQuantidade,
        #campoArea {
            display: none;
        }

        #resultado {
            display: none;
            margin-top: 28px;
            padding: 22px;
            border: 1px solid #d7e2da;
            border-radius: 8px;
            background: #f7faf8;
        }

        #resultado h3 {
            margin: 0 0 18px;
            font-size: 18px;
        }

        .destaque {
            margin-bottom: 18px;
            padding: 16px;
            background: #e9f2ec;
            border-radius: 7px;
        }

        .destaque small {
            display: block;
            color: #55705e;
            margin-bottom: 5px;
            font-size: 12px;
        }

        .destaque strong {
            font-size: 23px;
            color: #24543e;
        }

        .linha {
            padding: 10px 0;
            border-bottom: 1px solid #e4eae6;
            font-size: 14px;
            line-height: 1.4;
        }

        .linha:last-child {
            border-bottom: none;
        }

        .linha strong {
            display: inline-block;
            min-width: 165px;
        }

        .aviso {
            margin-top: 15px;
            padding: 12px;
            border-radius: 6px;
            background: #edf3ef;
            font-size: 13px;
            line-height: 1.5;
        }

        .aviso.estadual {
            background: #fff3df;
            color: #78501c;
        }

        .erro {
            margin-top: 15px;
            padding: 12px;
            border-radius: 6px;
            background: #fff0f0;
            color: #a52b2b;
            font-size: 14px;
        }

        .carregando {
            margin-top: 18px;
            color: #6b7770;
            font-size: 13px;
        }

        footer {
            text-align: center;
            padding: 20px;
            color: #7b8780;
            font-size: 12px;
        }

        @media (max-width: 550px) {
            .card {
                padding: 19px;
            }

            .linha strong {
                display: block;
                margin-bottom: 4px;
            }
        }
    </style>
</head>

<body>

<header>
    <h1>Licenciamento Ambiental</h1>
    <p>Sistema de enquadramento de atividades</p>
</header>

<main>
    <section class="card">

        <h2>Enquadramento ambiental</h2>

        <p class="subtitulo">
            Selecione a atividade e informe o parâmetro correspondente.
            O resultado será atualizado automaticamente.
        </p>

        <label for="atividade">Atividade / CODRAM</label>

        <select id="atividade">
            <option value="">Carregando atividades...</option>
        </select>

        <div id="campoQuantidade">

            <label for="quantidade">Número de cabeças</label>

            <input
                type="number"
                id="quantidade"
                min="1"
                step="1"
                placeholder="Informe a quantidade de aves"
            >

            <div class="ajuda">
                Informe o número total de aves de postura.
            </div>

        </div>

        <div id="campoArea">

            <label for="area">Área útil (m²)</label>

            <input
                type="number"
                id="area"
                min="0.01"
                step="any"
                placeholder="Informe a área útil"
            >

        </div>

        <div id="carregando" class="carregando" style="display:none;">
            Atualizando enquadramento...
        </div>

        <div id="resultado" aria-live="polite">
            <h3>Resultado do enquadramento</h3>
            <div id="dadosResultado"></div>
        </div>

    </section>
</main>

<footer>
    Sistema de Licenciamento Ambiental
</footer>

<script>
    const API = window.location.origin;

    const atividade = document.getElementById("atividade");
    const campoQuantidade = document.getElementById("campoQuantidade");
    const campoArea = document.getElementById("campoArea");
    const quantidade = document.getElementById("quantidade");
    const area = document.getElementById("area");
    const resultado = document.getElementById("resultado");
    const dadosResultado = document.getElementById("dadosResultado");
    const carregando = document.getElementById("carregando");

    let ultimaConsulta = 0;

    async function carregarAtividades() {
        try {
            const resposta = await fetch(
                `${API}/api/licenciamento/codrams?page=0&size=100`
            );

            if (!resposta.ok) {
                throw new Error("Não foi possível carregar as atividades.");
            }

            const dados = await resposta.json();

            atividade.innerHTML =
                '<option value="">Selecione uma atividade</option>';

            dados.content.forEach(item => {
                const opcao = document.createElement("option");
                opcao.value = item.id;
                opcao.textContent =
                    `${item.codram} - ${item.descricao}`;

                atividade.appendChild(opcao);
            });

        } catch (erro) {
            atividade.innerHTML =
                '<option value="">Erro ao carregar atividades</option>';

            mostrarErro(erro.message);
        }
    }

    function limparResultado() {
        resultado.style.display = "none";
        dadosResultado.innerHTML = "";
    }

    function mostrarErro(mensagem) {
        dadosResultado.innerHTML = "";

        const aviso = document.createElement("div");
        aviso.className = "erro";
        aviso.textContent = mensagem;

        dadosResultado.appendChild(aviso);
        resultado.style.display = "block";
    }

    function adicionarLinha(rotulo, valor) {
        const linha = document.createElement("div");
        linha.className = "linha";

        const titulo = document.createElement("strong");
        titulo.textContent = rotulo;

        const conteudo = document.createElement("span");
        conteudo.textContent = valor;

        linha.appendChild(titulo);
        linha.appendChild(conteudo);

        dadosResultado.appendChild(linha);
    }

    function formatarNumero(valor) {
        return Number(valor).toLocaleString("pt-BR");
    }

    async function atualizarEnquadramento() {
        const id = Number(atividade.value);

        limparResultado();

        if (!id) {
            carregando.style.display = "none";
            return;
        }

        const dados = {
            codram_id: id
        };

        if (id === 2) {
            if (!quantidade.value || Number(quantidade.value) <= 0) {
                carregando.style.display = "none";
                return;
            }

            dados.quantidade = Number(quantidade.value);
        }

        if (id === 1) {
            if (!area.value || Number(area.value) <= 0) {
                carregando.style.display = "none";
                return;
            }

            dados.area_util = Number(area.value);
        }

        const consultaAtual = ++ultimaConsulta;

        carregando.style.display = "block";

        try {
            const resposta = await fetch(
                `${API}/api/licenciamento/enquadrar`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(dados)
                }
            );

            const retorno = await resposta.json();

            if (consultaAtual !== ultimaConsulta) {
                return;
            }

            if (!resposta.ok) {
                throw new Error(
                    retorno.detail || "Erro no enquadramento."
                );
            }

            dadosResultado.innerHTML = "";

            adicionarLinha("Atividade:", retorno.atividade);
            adicionarLinha("CODRAM:", retorno.codram);

            if (retorno.quantidade !== undefined) {
                adicionarLinha(
                    "Número de cabeças:",
                    formatarNumero(retorno.quantidade)
                );
            }

            if (retorno.area_util !== undefined) {
                adicionarLinha(
                    "Área útil:",
                    formatarNumero(retorno.area_util) + " m²"
                );
            }

            const destaque = document.createElement("div");
            destaque.className = "destaque";

            const legenda = document.createElement("small");
            legenda.textContent = "PORTE ENQUADRADO";

            const porte = document.createElement("strong");
            porte.textContent = retorno.porte;

            destaque.appendChild(legenda);
            destaque.appendChild(porte);

            dadosResultado.appendChild(destaque);

            adicionarLinha("Faixa de porte:", retorno.faixa_porte);
            adicionarLinha(
                "Potencial poluidor:",
                retorno.potencial_poluidor
            );

            adicionarLinha("Competência:", retorno.competencia);

            if (retorno.indice_taxa !== undefined) {
                adicionarLinha(
                    "Índice para cálculo da taxa:",
                    retorno.indice_taxa
                );
            }

            const aviso = document.createElement("div");
            aviso.className = "aviso";

            if (retorno.competencia === "Estadual") {
                aviso.classList.add("estadual");
            }

            aviso.textContent = retorno.situacao;

            dadosResultado.appendChild(aviso);

            resultado.style.display = "block";

        } catch (erro) {
            if (consultaAtual === ultimaConsulta) {
                mostrarErro(erro.message);
            }

        } finally {
            if (consultaAtual === ultimaConsulta) {
                carregando.style.display = "none";
            }
        }
    }

    atividade.addEventListener("change", () => {
        campoQuantidade.style.display = "none";
        campoArea.style.display = "none";

        quantidade.value = "";
        area.value = "";

        limparResultado();

        if (atividade.value === "2") {
            campoQuantidade.style.display = "block";
            quantidade.focus();
        }

        if (atividade.value === "1") {
            campoArea.style.display = "block";
            area.focus();
        }
    });

    quantidade.addEventListener(
        "input",
        atualizarEnquadramento
    );

    area.addEventListener(
        "input",
        atualizarEnquadramento
    );

    carregarAtividades();
</script>

</body>
</html>
"""
