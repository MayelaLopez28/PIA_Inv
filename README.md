# PIA — Investigación de Operaciones | FCFM, UANL | Enero-Junio 2026

**Tema 17:** Problema de la Mochila para la Selección de Hardware en Racks de Servidores con Limitante Térmica

**Alumna:** Mayela Mayte López Cerino | **Matrícula:** 1953581  
**Empresa ficticia:** NorthGrid Colocation S.A. de C.V. — Cliente: ÁgilPay Fintech

---

## Estructura del repositorio

```
PIA_Inv/
├── script.py          # Modelo principal: PuLP + análisis de sensibilidad + visualizaciones
├── server.py          # API backend con FastAPI (conecta el frontend con el solver)
├── frontend/          # Interfaz interactiva React + Vite
│   ├── src/
│   │   └── App.jsx
│   └── package.json
└── README.md
```

---

## Requisitos previos

- **Python 3.10+**
- **Node.js 18+** y **npm**

---

## Parte 1 — Script Python (modelo + gráficas)

Este archivo ejecuta el modelo de optimización completo y genera el dashboard de visualizaciones.

### Instalar dependencias

```bash
pip install pulp pandas numpy matplotlib
```

### Ejecutar

```bash
python script.py
```

**Qué produce:**
- Imprime en consola la solución óptima (hardware seleccionado, SVO total, uso de recursos)
- Imprime los ítems no seleccionados y la razón de exclusión
- Genera y guarda `PIA_Mochila_Rack_Dashboard.png` con 5 gráficas

---

## Parte 2 — Interfaz interactiva (Frontend + Backend)

La interfaz permite ajustar el presupuesto y el límite térmico con sliders y ejecutar el solver en tiempo real.

Se necesitan **dos terminales abiertas al mismo tiempo**.

---

### Terminal 1 — Levantar el backend (FastAPI)

```bash
pip install fastapi uvicorn pulp pandas pydantic
```

```bash
uvicorn server:app --reload --port 8000
```

Verifica que esté corriendo entrando a: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Terminal 2 — Levantar el frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

Abre en tu navegador: [http://localhost:5173](http://localhost:5173)

---

## Cómo usar la interfaz

1. Ajusta el slider de **Presupuesto CAPEX** (rango: $300,000 — $1,500,000 MXN)
2. Ajusta el slider de **Límite Térmico** (rango: 2,000 — 15,000 W)
3. Haz clic en **Ejecutar Solver**
4. El dashboard muestra:
   - Hardware seleccionado con su SVO
   - Distribución de TDP por categoría (gráfica dona)
   - Barras de utilización de presupuesto, TDP y espacio en rack

---

## Parámetros base del caso de estudio

| Parámetro | Valor |
|---|---|
| Límite térmico del rack | 12,000 W (PDU 15 kVA × 0.80) |
| Presupuesto CAPEX | $850,000 MXN |
| Espacio disponible | 42 U |
| Componentes candidatos | 23 |
| Restricciones de negocio | Mínimo 1 switch + 1 appliance de seguridad |

---

## Tecnologías utilizadas

| Herramienta | Uso |
|---|---|
| `PuLP` | Solver de programación entera binaria (CBC) |
| `pandas` | Manipulación del catálogo de hardware |
| `matplotlib` | Dashboard de visualizaciones estático |
| `FastAPI` | API REST que expone el solver |
| `React + Vite` | Interfaz interactiva en el navegador |
| `Recharts` | Gráficas interactivas en el frontend |