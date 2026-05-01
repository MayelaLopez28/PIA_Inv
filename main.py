from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pulp
import pandas as pd
from pydantic import BaseModel
from script import hardware, cols

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OptimizeRequest(BaseModel):
    budget: float
    tdp: float


@app.post("/optimize")
async def optimize(req: OptimizeRequest):
    df = pd.DataFrame(hardware, columns=cols)
    n = len(df)

    # Definición del problema
    prob = pulp.LpProblem("Seleccion_Hardware_Rack", pulp.LpMaximize)
    x = [pulp.LpVariable(f"x_{i + 1}", cat="Binary") for i in range(n)]

    # Función Objetivo
    prob += pulp.lpSum(df["SVO"].iloc[i] * x[i] for i in range(n))

    # Restricciones
    prob += pulp.lpSum(df["TDP_W"].iloc[i] * x[i] for i in range(n)) <= req.tdp
    prob += pulp.lpSum(df["costo_MXN"].iloc[i] * x[i] for i in range(n)) <= req.budget
    prob += pulp.lpSum(df["rack_U"].iloc[i] * x[i] for i in range(n)) <= 42

    # Restricciones de Negocio
    idx_net = df[df["categoria"] == "Network"].index.tolist()
    prob += pulp.lpSum(x[i] for i in idx_net) >= 1
    idx_sec = df[df["categoria"] == "Security"].index.tolist()
    prob += pulp.lpSum(x[i] for i in idx_sec) >= 1

    # Resolver
    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    seleccionados = [
        {
            "nombre": df["nombre"].iloc[i],
            "categoria": df["categoria"].iloc[i],
            "SVO": int(df["SVO"].iloc[i]),
            "TDP_W": int(df["TDP_W"].iloc[i]),
            "costo_MXN": int(df["costo_MXN"].iloc[i])
        }
        for i in range(n) if pulp.value(x[i]) == 1
    ]

    return {
        "status": pulp.LpStatus[prob.status],
        "total_svo": int(pulp.value(prob.objective)),
        "selected_items": seleccionados,
        "usage": {
            "tdp": float(sum(df["TDP_W"].iloc[i] for i in range(n) if pulp.value(x[i]) == 1)),
            "cost": float(sum(df["costo_MXN"].iloc[i] for i in range(n) if pulp.value(x[i]) == 1)),
            "u": int(sum(df["rack_U"].iloc[i] for i in range(n) if pulp.value(x[i]) == 1))
        }
    }