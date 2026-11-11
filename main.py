
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import math
import re

app = FastAPI(
    title="API de Licenciamento Ambiental",
    description="Sistema de enquadramento ambiental municipal",
    version="0.3.0"
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
    licenca: str
    area_util: float | None = Field(default=None, gt=0)
    quantidade: int | None = Field(default=None, gt=0)


def validar_licenca(licenca):
    if licenca not in ["LP", "LI", "LO", "LPI"]:
        raise HTTPException(
            status_code=400,
            detail="Modalidade de licença inválida"
        )


def enquadrar_aves(quantidade, licenca):
    validar_licenca(licenca)

    if quantidade <= 1000:
        return {
            "porte": "Isento",
            "faixa_porte": "Até 1.000 cabeças",
            "competencia": "Isento de licenciamento",
            "licenca": licenca,
            "situacao": "Atividade isenta",
            "observacao": "Porte isento conforme os critérios cadastrados."
        }

    elif quantidade <= 40000:
        porte = "Mínimo"
        faixa = "De 1.001 até 40.000 cabeças"
        indice = 1

    elif quantidade <= 80000:
        porte = "Pequeno"
        faixa = "De 40.001 até 80.000 cabeças"
        indice = 2

    elif quantidade <= 120000:
        porte = "Médio"
        faixa = "De 80.001 até 120.000 cabeças"
        indice = 3

    elif quantidade <= 160000:
        return {
            "porte": "Grande",
            "faixa_porte": "De 120.001 até 160.000 cabeças",
            "competencia": "Estadual",
            "licenca": licenca,
            "situacao": "Licenciamento de competência do órgão ambiental estadual."
        }

    else:
        return {
            "porte": "Excepcional",
            "faixa_porte": "Acima de 160.000 cabeças",
            "competencia": "Estadual",
            "licenca": licenca,
            "situacao": "Licenciamento de competência do órgão ambiental estadual."
        }

    return {
        "porte": porte,
        "faixa_porte": faixa,
        "competencia": "Municipal",
        "licenca": licenca,
        "indice_taxa": indice,
        "situacao": "Licenciamento municipal"
    }


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


@app.get("/", response_class=HTMLResponse)
def pagina_inicial():
    return HTML


@app.get("/api/health")
def health():
    return {
        "sistema": "API de Licenciamento Ambiental",
        "status": "online",
        "versao": "0.3.0"
    }


@app.get("/api/licenciamento/codrams")
def listar_codrams(
    page: int = Query(default=0, ge=0),
    size: int = Query(default=10, ge=1, le=100),
    search: str = ""
):
    resultados = [
        item for item in ATIVIDADES
        if item["ativo"]
    ]

    termos = interpretar_busca(search)

    for campo, valor in termos:
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
            detail="Atividade não encontrada"
        )

    if dados.codram_id == 2:
        if dados.quantidade is None:
            raise HTTPException(
                status_code=400,
                detail="Informe o número de cabeças."
            )

        resultado = enquadrar_aves(
            dados.quantidade,
            dados.licenca
        )

        return {
            "atividade": atividade["descricao"],
            "codram": atividade["codram"],
            "quantidade": dados.quantidade,
            "unidade": atividade["unidade"],
            "potencial_poluidor": atividade["potencial_poluidor"],
            **resultado
        }

    if dados.codram_id == 1:
        validar_licenca(dados.licenca)

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
            "licenca": dados.licenca,
            "situacao": "Enquadramento demonstrativo",
            "observacao": "Regras fictícias para testes."
        }

    raise HTTPException(
        status_code=400,
        detail="Atividade sem regra de enquadramento cadastrada."
    )


@app.post("/api/licenciamento/enquadrar-atividade")
def enquadrar_atividade(dados: DadosEnquadramento):
    if dados.codram_id != 2:
        raise HTTPException(
            status_code=400,
            detail="Este endpoint está configurado para o CODRAM 112,12."
        )

    return enquadrar(dados)


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
            padding: 26px 20px;
        }

        header h1 {
            margin: 0;
            font-size: 23px;
            font-weight: 600;
        }

        header p {
            margin: 7px 0 0;
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

        button {
            width: 100%;
            margin-top: 25px;
            padding: 14px;
            border: none;
            border-radius: 6px;
            background: #24543e;
            color: white;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
        }

        button:hover {
            background: #193f2d;
        }

        button:disabled {
            opacity: 0.6;
            cursor: wait;
        }

        #resultado {
            display: none;
            margin-top: 25px;
            padding: 20px;
            border: 1px solid #d7e2da;
            border-radius: 8px;
            background: #f7faf8;
        }

        #resultado h3 {
            margin: 0 0 16px;
            font-size: 18px;
        }

        .linha {
            padding: 9px 0;
            border-bottom: 1px solid #e4eae6;
            font-size: 14px;
        }

        .linha:last-child {
            border-bottom: none;
        }

        .linha strong {
            display: inline-block;
            min-width: 145px;
        }

        .mensagem {
            margin-top: 15px;
            padding: 12px;
            border-radius: 6px;
            background: #edf3ef;
            font-size: 14px;
        }

        .erro {
            color: #a52b2b;
            background: #fff0f0;
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
            Selecione a atividade e informe os dados para calcular o enquadramento.
        </p>

        <form id="formulario">

            <label for="atividade">Atividade / CODRAM</label>
            <select id="atividade" required>
                <option value="">Carregando atividades...</option>
            </select>

            <div id="campoQuantidade" style="display:none;">
                <label for="quantidade">Número de cabeças</label>
                <input
                    type="number"
                    id="quantidade"
                    min="1"
                    step="1"
                    placeholder="Informe a quantidade de aves"
                >
            </div>

            <div id="campoArea" style="display:none;">
                <label for="area">Área útil (m²)</label>
                <input
                    type="number"
                    id="area"
                    min="0.01"
                    step="any"
                    placeholder="Informe a área útil"
                >
            </div>

            <label for="licenca">Modalidade de licença</label>
            <select id="licenca" required>
                <option value="">Selecione</option>
                <option value="LP">LP - Licença Prévia</option>
                <option value="LI">LI - Licença de Instalação</option>
                <option value="LO">LO - Licença de Operação</option>
                <option value="LPI">LPI - Licença Prévia e de Instalação</option>
            </select>

            <button type="submit" id="botao">
                Calcular enquadramento
            </button>
        </form>

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
    const formulario = document.getElementById("formulario");
    const resultado = document.getElementById("resultado");
    const dadosResultado = document.getElementById("dadosResultado");
    const botao = document.getElementById("botao");

    async function carregarAtividades() {
        try {
            const resposta = await fetch(
                `${API}/api/licenciamento/codrams?page=0&size=100`
            );

            if (!resposta.ok) {
                throw new Error("Não foi possível carregar as atividades.");
            }

            const dados = await resposta.json();

            atividade.innerHTML = '<option value="">Selecione uma atividade</option>';

            dados.content.forEach(item => {
                const opcao = document.createElement("option");
                opcao.value = item.id;
                opcao.textContent = `${item.codram} - ${item.descricao}`;
                atividade.appendChild(opcao);
            });

        } catch (erro) {
            atividade.innerHTML = '<option value="">Erro ao carregar atividades</option>';
            alert(erro.message);
        }
    }

    atividade.addEventListener("change", () => {
        campoQuantidade.style.display = "none";
        campoArea.style.display = "none";

        quantidade.required = false;
        area.required = false;

        resultado.style.display = "none";

        if (atividade.value === "2") {
            campoQuantidade.style.display = "block";
            quantidade.required = true;
        }

        if (atividade.value === "1") {
            campoArea.style.display = "block";
            area.required = true;
        }
    });

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

    formulario.addEventListener("submit", async (evento) => {
        evento.preventDefault();

        resultado.style.display = "none";
        dadosResultado.innerHTML = "";

        const id = Number(atividade.value);

        if (!id) {
            alert("Selecione uma atividade.");
            return;
        }

        const dados = {
            codram_id: id,
            licenca: document.getElementById("licenca").value
        };

        if (id === 2) {
            dados.quantidade = Number(quantidade.value);
        }

        if (id === 1) {
            dados.area_util = Number(area.value);
        }

        botao.disabled = true;
        botao.textContent = "Calculando...";

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

            if (!resposta.ok) {
                throw new Error(
                    retorno.detail || "Erro ao calcular enquadramento."
                );
            }

            adicionarLinha("Atividade:", retorno.atividade);
            adicionarLinha("CODRAM:", retorno.codram);

            if (retorno.quantidade !== undefined) {
                adicionarLinha(
                    "Número de cabeças:",
                    retorno.quantidade.toLocaleString("pt-BR")
                );
            }

            if (retorno.area_util !== undefined) {
                adicionarLinha(
                    "Área útil:",
                    retorno.area_util + " m²"
                );
            }

            adicionarLinha("Porte:", retorno.porte);
            adicionarLinha("Faixa de porte:", retorno.faixa_porte);
            adicionarLinha("Potencial poluidor:", retorno.potencial_poluidor);
            adicionarLinha("Competência:", retorno.competencia);
            adicionarLinha("Licença:", retorno.licenca);

            if (retorno.indice_taxa !== undefined) {
                adicionarLinha(
                    "Índice para cálculo da taxa:",
                    retorno.indice_taxa
                );
            }

            adicionarLinha("Situação:", retorno.situacao);

            if (retorno.observacao) {
                const mensagem = document.createElement("div");
                mensagem.className = "mensagem";
                mensagem.textContent = retorno.observacao;
                dadosResultado.appendChild(mensagem);
            }

            resultado.style.display = "block";

        } catch (erro) {
            dadosResultado.innerHTML = "";

            const mensagem = document.createElement("div");
            mensagem.className = "mensagem erro";
            mensagem.textContent = erro.message;

            dadosResultado.appendChild(mensagem);
            resultado.style.display = "block";

        } finally {
            botao.disabled = false;
            botao.textContent = "Calcular enquadramento";
        }
    });

    carregarAtividades();
</script>

</body>
</html>
"""
