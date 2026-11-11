
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="API de Licenciamento Ambiental",
    description="Sistema de enquadramento ambiental municipal",
    version="0.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# =====================================================
# CADASTRO DE ATIVIDADES (CODRAM)
# =====================================================

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
        "descricao": "CRIAÇÃO DE AVES DE POSTURA",
        "parametro": "Número de cabeças",
        "unidade": "un",
        "potencial_poluidor": "Médio",
        "ativo": True
    }
]


# =====================================================
# MODELOS DE DADOS
# =====================================================

class DadosEnquadramento(BaseModel):
    codram_id: int
    area_util: float = Field(gt=0)
    licenca: str


class DadosAvesPostura(BaseModel):
    codram_id: int
    quantidade: int = Field(ge=0)


# =====================================================
# PÁGINA INICIAL
# =====================================================

@app.get("/")
def inicio():
    return {
        "sistema": "API de Licenciamento Ambiental",
        "status": "online",
        "ambiente": "producao"
    }


# =====================================================
# LISTAGEM DE CODRAMS
# =====================================================

@app.get("/api/licenciamento/codrams")
def listar_codrams(search: str = ""):

    resultados = [
        item for item in ATIVIDADES
        if item["ativo"] and search.lower() in (
            item["codram"] + " " + item["descricao"]
        ).lower()
    ]

    return {
        "content": resultados,
        "page": 0,
        "size": len(resultados)
    }


# =====================================================
# ENQUADRAMENTO DEMONSTRATIVO POR ÁREA
# MANTIDO PARA PRESERVAR A FUNÇÃO EXISTENTE
# =====================================================

@app.post("/api/licenciamento/enquadrar")
def enquadrar(dados: DadosEnquadramento):

    atividade = next(
        (item for item in ATIVIDADES
         if item["id"] == dados.codram_id),
        None
    )

    if not atividade:
        raise HTTPException(
            status_code=404,
            detail="Atividade não encontrada"
        )

    if dados.licenca not in ["LP", "LI", "LO", "LPI"]:
        raise HTTPException(
            status_code=400,
            detail="Modalidade de licença inválida"
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
        "taxa": None,
        "situacao": "Enquadramento demonstrativo",
        "observacao": "Regras fictícias para testes."
    }


# =====================================================
# ENQUADRAMENTO - CODRAM 112,12
# CRIAÇÃO DE AVES DE POSTURA
# =====================================================

@app.post("/api/licenciamento/enquadrar-atividade")
def enquadrar_atividade(dados: DadosAvesPostura):

    atividade = next(
        (
            item for item in ATIVIDADES
            if item["id"] == dados.codram_id
            and item["ativo"]
        ),
        None
    )

    if not atividade:
        raise HTTPException(
            status_code=404,
            detail="Atividade não encontrada ou inativa"
        )

    if atividade["codram"] != "112,12":
        raise HTTPException(
            status_code=400,
            detail="Esta atividade ainda não possui regra de enquadramento cadastrada."
        )

    quantidade = dados.quantidade

    # ENQUADRAMENTO DOS PORTES

    if quantidade <= 1000:

        porte = "Isento"
        faixa = "Até 1.000 cabeças"
        competencia = "Isento"

    elif quantidade <= 40000:

        porte = "Mínimo"
        faixa = "De 1.001 até 40.000 cabeças"
        competencia = "Municipal"

    elif quantidade <= 80000:

        porte = "Pequeno"
        faixa = "De 40.001 até 80.000 cabeças"
        competencia = "Municipal"

    elif quantidade <= 120000:

        porte = "Médio"
        faixa = "De 80.001 até 120.000 cabeças"
        competencia = "Municipal"

    elif quantidade <= 160000:

        porte = "Grande"
        faixa = "De 120.001 até 160.000 cabeças"
        competencia = "Estadual"

    else:

        porte = "Excepcional"
        faixa = "Acima de 160.000 cabeças"
        competencia = "Estadual"

    # RESULTADO BÁSICO

    resultado = {
        "atividade": atividade["descricao"],
        "codram": atividade["codram"],
        "quantidade": quantidade,
        "parametro": atividade["parametro"],
        "unidade": atividade["unidade"],
        "potencial_poluidor": atividade["potencial_poluidor"],
        "porte": porte,
        "faixa_porte": faixa,
        "competencia": competencia
    }

    # TAXA SOMENTE PARA ENQUADRAMENTO MUNICIPAL
    # PARA PORTE ISENTO, O ÍNDICE É ZERO.
    # PARA COMPETÊNCIA ESTADUAL, NÃO RETORNA TAXA.

    if competencia == "Isento":

        resultado["indice_taxa"] = 0
        resultado["situacao"] = "Isento"

    elif competencia == "Municipal":

        indice_taxa = {
            "Mínimo": 1,
            "Pequeno": 2,
            "Médio": 3
        }

        resultado["indice_taxa"] = indice_taxa[porte]
        resultado["situacao"] = "Licenciamento municipal"

    else:

        resultado["situacao"] = (
            "Licenciamento de competência do órgão ambiental estadual."
        )

    return resultado
