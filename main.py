
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="API de Licenciamento Ambiental",
    description="Protótipo de enquadramento ambiental municipal",
    version="0.1.0"
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
        "ativo": True
    }
]


class DadosEnquadramento(BaseModel):
    codram_id: int
    area_util: float = Field(gt=0)
    licenca: str


@app.get("/")
def inicio():
    return {
        "sistema": "API de Licenciamento Ambiental",
        "status": "online",
        "ambiente": "demonstracao"
    }


@app.get("/api/licenciamento/codrams")
def listar_codrams(search: str = ""):
    resultados = [
        item for item in ATIVIDADES
        if search.lower() in (
            item["codram"] + " " + item["descricao"]
        ).lower()
    ]

    return {
        "content": resultados,
        "page": 0,
        "size": len(resultados)
    }


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
