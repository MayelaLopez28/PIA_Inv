# =============================================================================
# PIA - Investigación de Operaciones | FCFM, UANL | Enero-Junio 2026
# Tema 17: Problema de la Mochila para la selección de hardware
#          en racks de servidores con limitante térmica
# =============================================================================
# DECLARACIÓN DE ORIGINALIDAD:
# El alumno declara que comprende y es capaz de explicar cada línea del
# presente código. El escenario y los datos fueron construidos con criterio
# propio; el código fue desarrollado con apoyo de herramientas de asistencia,
# pero su lógica, parámetros y conclusiones son de autoría y responsabilidad
# del alumno.
# =============================================================================

import pulp
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# Seccion 1: Definicion de datos
# Empresa ficticia: NorthGrid Colocation S.A. de C.V., Monterrey, NL
# Cliente: Fintech "ÁgilPay" — necesita rack dedicado de alta densidad
# Restricciones del rack:
#   - Límite térmico (TDP): 12,000 W por rack (PDU de 15 kVA, factor 0.80)
#   - Presupuesto CAPEX: $850,000 MXN
#   - Unidades de rack disponibles (U): 42U por rack
#   - El cliente quiere maximizar el "Score de Valor Operativo" (SVO),
#     un índice compuesto por rendimiento, disponibilidad y ROI esperado.
# =============================================================================

# --- Catalogo de hardware disponible ---
# Cada componente tiene:
#   nombre, categoria, TDP (W), costo (MXN), unidades de rack (U), SVO (puntos)

hardware = [
    # (id, nombre, categoría, TDP_W, costo_MXN, rack_U, SVO)

    # ---- Servidores de computo ----
    ( 1, "Dell PowerEdge R760 (2x Xeon Gold 6448Y, 512 GB RAM)",    "Servidor",   400, 145_000, 2, 92),
    ( 2, "HPE ProLiant DL380 Gen11 (2x Xeon Silver 4416+, 256 GB)", "Servidor",   350,  98_000, 2, 78),
    ( 3, "Supermicro SYS-221H (2x AMD EPYC 9354, 512 GB RAM)",      "Servidor",   480, 162_000, 2, 97),
    ( 4, "Dell PowerEdge R660 (1x Xeon Gold 6430, 128 GB RAM)",     "Servidor",   250,  72_000, 1, 61),
    ( 5, "HPE ProLiant DL360 Gen11 (1x Xeon Silver 4410Y, 64 GB)",  "Servidor",   185,  48_000, 1, 45),

    # ---- Servidores GPU / IA ----
    ( 6, "NVIDIA DGX H100 (8x H100 80 GB SXM5)",                    "GPU/IA",    6500, 420_000, 8, 99),
    ( 7, "Dell PowerEdge XE9680 (8x NVIDIA A100 80 GB)",            "GPU/IA",    5600, 385_000, 8, 95),
    ( 8, "Supermicro SYS-420GP-TNR (4x NVIDIA L40S 48 GB)",         "GPU/IA",    1600, 210_000, 4, 82),
    ( 9, "HPE ProLiant DL380 Gen11 + 2x NVIDIA A30",                "GPU/IA",     750, 135_000, 2, 70),

    # ---- Almacenamiento (SAN / NAS) ----
    (10, "Pure Storage FlashArray//XL 170 (460 TB NVMe)",           "Storage",    680, 198_000, 4, 88),
    (11, "Dell PowerVault ME5024 (192 TB SAS, RAID 6)",             "Storage",    320,  87_000, 2, 65),
    (12, "Synology RS3621xs+ (288 TB HDD + SSD cache)",             "Storage",    120,  34_000, 2, 42),
    (13, "QNAP TES-3085U (120 TB NVMe híbrido)",                    "Storage",     95,  22_000, 2, 36),

    # ---- Networking ----
    (14, "Cisco Nexus 93180YC-FX3 (48x 25GbE + 6x 100GbE)",        "Network",    380,  95_000, 1, 74),
    (15, "Arista 7050CX3-32S (32x 100GbE QSFP28)",                  "Network",    325,  88_000, 1, 71),
    (16, "Juniper QFX5120-48Y (48x 25GbE + 8x 100GbE)",             "Network",    290,  76_000, 1, 68),
    (17, "Cisco Catalyst 9300L-48T (switch de acceso 1GbE)",        "Network",    110,  18_000, 1, 32),

    # ---- Seguridad / Appliances ----
    (18, "Palo Alto PA-5450 (NGFW, 120 Gbps)",                      "Security",   550, 115_000, 2, 80),
    (19, "Fortinet FortiGate 600F (NGFW, 40 Gbps)",                 "Security",   220,  62_000, 1, 58),
    (20, "F5 BIG-IP i5800 (Load Balancer, 40 Gbps)",                "Security",   300,  78_000, 2, 66),

    # ---- Adminictracion / Out-of-band ----
    (21, "APC Smart-UPS SRTL10KRM4UI (10 kVA, Online)",             "Admin",      120,  45_000, 3, 40),
    (22, "Raritan Dominion KX III-832 (KVM 32 puertos)",            "Admin",       35,  12_000, 1, 22),
    (23, "Vertiv Avocent ACS 8000 (Console Server, 48p)",           "Admin",       25,   9_500, 1, 18),
]

# Convertir a DataFrame
cols = ["id","nombre","categoria","TDP_W","costo_MXN","rack_U","SVO"]
df = pd.DataFrame(hardware, columns=cols)

# =============================================================================
# Seccion 2: Parametros del problema
# =============================================================================

TDP_MAX    = 12_000   # Watts — límite térmico del rack (PDU 15 kVA × 0.80)
BUDGET_MAX = 850_000  # MXN   — presupuesto CAPEX del cliente ÁgilPay
RACK_U_MAX = 42       # U     — unidades de rack físicas disponibles

n = len(df)  # número de ítems candidatos

# =============================================================================
# Seccion 3: Modelado matematico
# =============================================================================
# Problema de la mochila multi-restriccion (0/1 Knapsack)
#
# Variables de decisión:
#   x_i ∈ {0, 1}   ∀ i = 1,...,n
#   x_i = 1 → el ítem i SE INSTALA en el rack
#   x_i = 0 → el ítem i NO se instala
#
# Función objetivo (MAXIMIZAR Score de Valor Operativo total):
#   MAX  Σ SVO_i · x_i
#
# Sujeto a:
#   (R1) Σ TDP_i  · x_i  ≤ TDP_MAX      (restricción térmica)
#   (R2) Σ costo_i · x_i ≤ BUDGET_MAX   (restricción presupuestal)
#   (R3) Σ U_i    · x_i  ≤ RACK_U_MAX   (restricción de espacio físico)
#   (R4) x_i ∈ {0, 1}                   (integralidad binaria)
#
# Restricciones de negocio (lógicas):
#   (R5) Al menos 1 switch de red debe seleccionarse
#   (R6) Al menos 1 appliance de seguridad debe seleccionarse
# =============================================================================

if __name__ == "__main__":
    print("=" * 65)
    print("  NorthGrid Colocation — Optimización de Rack para ÁgilPay")
    print("=" * 65)
    print(f"\n  Ítems candidatos   : {n}")
    print(f"  Límite térmico     : {TDP_MAX:,} W")
    print(f"  Presupuesto CAPEX  : ${BUDGET_MAX:,} MXN")
    print(f"  Espacio disponible : {RACK_U_MAX} U\n")

    # =============================================================================
    # Seccion 4: Resolucion con PuLP
    # =============================================================================

    prob = pulp.LpProblem("Seleccion_Hardware_Rack", pulp.LpMaximize)

    # Variables de decisión binarias
    x = [pulp.LpVariable(f"x_{i+1}", cat="Binary") for i in range(n)]

    # Función objetivo
    prob += pulp.lpSum(df["SVO"].iloc[i] * x[i] for i in range(n)), "Maximizar_SVO_Total"

    # Restricciones principales
    prob += pulp.lpSum(df["TDP_W"].iloc[i]   * x[i] for i in range(n)) <= TDP_MAX,    "R1_Termica"
    prob += pulp.lpSum(df["costo_MXN"].iloc[i] * x[i] for i in range(n)) <= BUDGET_MAX, "R2_Presupuesto"
    prob += pulp.lpSum(df["rack_U"].iloc[i]  * x[i] for i in range(n)) <= RACK_U_MAX, "R3_Espacio"

    # Restricciones lógicas de negocio
    # R5: al menos 1 switch de red (IDs 14,15,16,17 → índices 13,14,15,16)
    idx_net = df[df["categoria"] == "Network"].index.tolist()
    prob += pulp.lpSum(x[i] for i in idx_net) >= 1, "R5_MinRed"

    # R6: al menos 1 appliance de seguridad (IDs 18,19,20 → índices 17,18,19)
    idx_sec = df[df["categoria"] == "Security"].index.tolist()
    prob += pulp.lpSum(x[i] for i in idx_sec) >= 1, "R6_MinSeguridad"

    # Resolver
    status = prob.solve(pulp.PULP_CBC_CMD(msg=0))

    print(f"  Estado del solver  : {pulp.LpStatus[status]}")

    # =============================================================================
    # Seccion 5: Extraccion de resultados
    # =============================================================================

    seleccionados = [i for i in range(n) if pulp.value(x[i]) == 1]
    df_sel = df.iloc[seleccionados].copy()

    total_SVO    = int(pulp.value(prob.objective))
    total_TDP    = df_sel["TDP_W"].sum()
    total_costo  = df_sel["costo_MXN"].sum()
    total_U      = df_sel["rack_U"].sum()

    uso_tdp      = total_TDP / TDP_MAX * 100
    uso_presup   = total_costo / BUDGET_MAX * 100
    uso_rack     = total_U / RACK_U_MAX * 100

    print("\n" + "=" * 65)
    print("  SOLUCIÓN ÓPTIMA — Hardware seleccionado para el rack")
    print("=" * 65)
    print(df_sel[["nombre","categoria","TDP_W","costo_MXN","rack_U","SVO"]].to_string(index=False))
    print("\n" + "-" * 65)
    print(f"  SVO Total          : {total_SVO} puntos")
    print(f"  TDP consumido      : {total_TDP:,} W  / {TDP_MAX:,} W  ({uso_tdp:.1f}%)")
    print(f"  Costo CAPEX        : ${total_costo:,} MXN / ${BUDGET_MAX:,} MXN ({uso_presup:.1f}%)")
    print(f"  Espacio utilizado  : {total_U} U / {RACK_U_MAX} U ({uso_rack:.1f}%)")
    print("=" * 65)

    # =============================================================================
    # Seccion 6: Analisis de sensibilidad
    # ¿Qué pasa si aumentamos el límite térmico del rack en 1,000 W?
    # Simulamos variaciones del TDP_MAX de ±3,000 W en pasos de 500 W
    # =============================================================================

    tdp_vals   = list(range(9_000, 15_001, 500))
    svo_vals   = []
    tdp_used   = []
    cost_used  = []

    for tdp_limit in tdp_vals:
        p2 = pulp.LpProblem(f"sens_{tdp_limit}", pulp.LpMaximize)
        y  = [pulp.LpVariable(f"y_{i}", cat="Binary") for i in range(n)]
        p2 += pulp.lpSum(df["SVO"].iloc[i]      * y[i] for i in range(n))
        p2 += pulp.lpSum(df["TDP_W"].iloc[i]    * y[i] for i in range(n)) <= tdp_limit
        p2 += pulp.lpSum(df["costo_MXN"].iloc[i]* y[i] for i in range(n)) <= BUDGET_MAX
        p2 += pulp.lpSum(df["rack_U"].iloc[i]   * y[i] for i in range(n)) <= RACK_U_MAX
        idx_n2 = df[df["categoria"] == "Network"].index.tolist()
        idx_s2 = df[df["categoria"] == "Security"].index.tolist()
        p2 += pulp.lpSum(y[i] for i in idx_n2) >= 1
        p2 += pulp.lpSum(y[i] for i in idx_s2) >= 1
        p2.solve(pulp.PULP_CBC_CMD(msg=0))
        sels = [i for i in range(n) if pulp.value(y[i]) == 1]
        svo_vals.append(int(pulp.value(p2.objective)) if pulp.value(p2.objective) else 0)
        tdp_used.append(df.iloc[sels]["TDP_W"].sum())
        cost_used.append(df.iloc[sels]["costo_MXN"].sum())

    # =============================================================================
    # Seccion 7: Visualizaciones
    # =============================================================================

    colores_cat = {
        "Servidor" : "#1B6CA8",
        "GPU/IA"   : "#C0392B",
        "Storage"  : "#27AE60",
        "Network"  : "#8E44AD",
        "Security" : "#E67E22",
        "Admin"    : "#7F8C8D",
    }

    fig = plt.figure(figsize=(18, 14))
    fig.patch.set_facecolor("#0D1117")
    gs  = GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

    TEXT_COLOR = "#E8EAF0"
    GRID_COLOR = "#2A2D35"
    ACCENT     = "#00D4FF"

    plt.rcParams.update({
        "text.color": TEXT_COLOR,
        "axes.labelcolor": TEXT_COLOR,
        "xtick.color": TEXT_COLOR,
        "ytick.color": TEXT_COLOR,
    })

    # ---- Grafica 1: Barras horizontales — SVO por componente seleccionado ----
    ax1 = fig.add_subplot(gs[0, :2])
    ax1.set_facecolor("#161B22")
    nombres_cortos = [n[:38]+"…" if len(n)>38 else n for n in df_sel["nombre"]]
    colores_barras = [colores_cat[c] for c in df_sel["categoria"]]
    bars = ax1.barh(nombres_cortos, df_sel["SVO"], color=colores_barras,
                    edgecolor="#0D1117", linewidth=0.8, height=0.7)
    for bar, val in zip(bars, df_sel["SVO"]):
        ax1.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                 f"{val}", va="center", ha="left", fontsize=9, color=TEXT_COLOR, fontweight="bold")
    ax1.set_xlabel("Score de Valor Operativo (SVO)", color=TEXT_COLOR)
    ax1.set_title("Hardware seleccionado — SVO por componente", color=ACCENT,
                  fontsize=13, fontweight="bold", pad=10)
    ax1.set_xlim(0, 110)
    ax1.grid(axis="x", color=GRID_COLOR, linestyle="--", alpha=0.5)
    ax1.set_facecolor("#161B22")
    for sp in ax1.spines.values(): sp.set_color(GRID_COLOR)

    handles = [mpatches.Patch(color=v, label=k) for k,v in colores_cat.items()]
    ax1.legend(handles=handles, loc="lower right", fontsize=8,
               facecolor="#0D1117", edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR)

    # ---- Grafica 2: Donut — distribución TDP por categoría ----
    ax2 = fig.add_subplot(gs[0, 2])
    ax2.set_facecolor("#161B22")
    tdp_cat = df_sel.groupby("categoria")["TDP_W"].sum()
    colores_donut = [colores_cat[c] for c in tdp_cat.index]
    wedges, texts, autotexts = ax2.pie(
        tdp_cat.values, labels=None, colors=colores_donut,
        autopct="%1.1f%%", startangle=140,
        wedgeprops=dict(width=0.55, edgecolor="#0D1117", linewidth=1.5),
        pctdistance=0.78, textprops={"color": TEXT_COLOR, "fontsize": 8}
    )
    for at in autotexts: at.set_fontweight("bold")
    ax2.text(0, 0, f"{total_TDP:,}\nW", ha="center", va="center",
             fontsize=10, color=TEXT_COLOR, fontweight="bold")
    ax2.set_title("TDP por categoría", color=ACCENT, fontsize=12, fontweight="bold")

    # ---- Grafica 3: Gauge de utilización de recursos ----
    ax3 = fig.add_subplot(gs[1, :])
    ax3.set_facecolor("#161B22")
    ax3.set_xlim(0, 1)
    ax3.set_ylim(-0.2, 1)
    ax3.axis("off")
    ax3.set_title("Utilización de recursos vs. capacidad disponible", color=ACCENT,
                  fontsize=13, fontweight="bold")

    recursos = [
        ("Límite Térmico (W)", uso_tdp/100, f"{total_TDP:,} / {TDP_MAX:,} W", "#E74C3C"),
        ("Presupuesto CAPEX (MXN)", uso_presup/100, f"${total_costo:,} / ${BUDGET_MAX:,}", "#F39C12"),
        ("Espacio en Rack (U)", uso_rack/100, f"{total_U} / {RACK_U_MAX} U", "#2ECC71"),
    ]

    bar_h = 0.18
    for idx, (label, pct, detail, color) in enumerate(recursos):
        y_pos = 0.75 - idx * 0.32
        ax3.barh(y_pos, 1, height=bar_h, color="#2A2D35", left=0, zorder=1)
        ax3.barh(y_pos, pct, height=bar_h, color=color, left=0, zorder=2, alpha=0.9)
        ax3.text(-0.01, y_pos, label, ha="right", va="center",
                 fontsize=10, color=TEXT_COLOR, fontweight="bold")
        ax3.text(pct + 0.01, y_pos, f"{pct*100:.1f}%  ({detail})",
                 ha="left", va="center", fontsize=9, color=TEXT_COLOR)

    # ---- Grafica 4: Analisis de sensibilidad ----
    ax4 = fig.add_subplot(gs[2, :2])
    ax4.set_facecolor("#161B22")
    ax4.plot(tdp_vals, svo_vals, color=ACCENT, marker="o", markersize=5,
             linewidth=2.2, label="SVO Óptimo")
    ax4.axvline(TDP_MAX, color="#E74C3C", linestyle="--", linewidth=1.5,
                label=f"TDP actual ({TDP_MAX:,} W)")
    ax4.axhline(total_SVO, color="#F39C12", linestyle=":", linewidth=1.5,
                label=f"SVO actual ({total_SVO} pts)")
    ax4.fill_between(tdp_vals, svo_vals, alpha=0.12, color=ACCENT)
    ax4.set_xlabel("Límite Térmico del Rack (W)", color=TEXT_COLOR)
    ax4.set_ylabel("Score de Valor Operativo Total", color=TEXT_COLOR)
    ax4.set_title("Análisis de Sensibilidad — Impacto del Límite Térmico en SVO",
                  color=ACCENT, fontsize=12, fontweight="bold")
    ax4.legend(facecolor="#0D1117", edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR, fontsize=9)
    ax4.grid(color=GRID_COLOR, linestyle="--", alpha=0.4)
    for sp in ax4.spines.values(): sp.set_color(GRID_COLOR)

    # ---- Grafica 5: Tabla resumen ----
    ax5 = fig.add_subplot(gs[2, 2])
    ax5.set_facecolor("#161B22")
    ax5.axis("off")
    ax5.set_title("Resumen Ejecutivo", color=ACCENT, fontsize=12, fontweight="bold")
    resumen = [
        ["Métrica", "Valor"],
        ["SVO Total", f"{total_SVO} pts"],
        ["Componentes", f"{len(df_sel)}"],
        ["TDP usado", f"{uso_tdp:.1f}%"],
        ["Presupuesto", f"{uso_presup:.1f}%"],
        ["Rack usado", f"{uso_rack:.1f}%"],
        ["Holgura TDP", f"{TDP_MAX-total_TDP:,} W"],
        ["Ahorro", f"${BUDGET_MAX-total_costo:,}"],
    ]
    tbl = ax5.table(cellText=resumen[1:], colLabels=resumen[0],
                    cellLoc="center", loc="center",
                    bbox=[0.0, 0.05, 1.0, 0.9])
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    for (row, col), cell in tbl.get_celld().items():
        cell.set_facecolor("#1B2030" if row % 2 == 0 else "#0D1117")
        cell.set_text_props(color=TEXT_COLOR)
        cell.set_edgecolor(GRID_COLOR)
        if row == 0:
            cell.set_facecolor("#1B3A5C")
            cell.set_text_props(color=ACCENT, fontweight="bold")

    fig.suptitle(
        "NorthGrid Colocation — Optimización de Rack para ÁgilPay\n"
        "Problema de la Mochila Multirestricciones | PIA Investigación de Operaciones 2026",
        color=TEXT_COLOR, fontsize=14, fontweight="bold", y=0.98
    )

    plt.savefig("PIA_Mochila_Rack_Dashboard.png", dpi=150,
                bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.show()
    print("\n  Gráfica guardada: PIA_Mochila_Rack_Dashboard.png")

    # =============================================================================
    # Seccion 8: Analisis de items no selecconados (¿Por qué quedaron fuera?)
    # =============================================================================

    no_sel_idx = [i for i in range(n) if i not in seleccionados]
    df_no_sel  = df.iloc[no_sel_idx].copy()

    print("\n" + "=" * 65)
    print("  Ítems NO seleccionados y restricción activa que los excluye")
    print("=" * 65)
    for _, row in df_no_sel.iterrows():
        razones = []
        if total_TDP + row["TDP_W"] > TDP_MAX:
            razones.append(f"TDP excede en {total_TDP + row['TDP_W'] - TDP_MAX:,} W")
        if total_costo + row["costo_MXN"] > BUDGET_MAX:
            razones.append(f"Presupuesto excede en ${total_costo + row['costo_MXN'] - BUDGET_MAX:,}")
        if total_U + row["rack_U"] > RACK_U_MAX:
            razones.append(f"Espacio excede en {total_U + row['rack_U'] - RACK_U_MAX} U")
        if not razones:
            razones.append("Combinación subóptima vs. SVO")
        print(f"  ✗ {row['nombre'][:50]:<52} | {'; '.join(razones)}")

    print("\n  Fin del análisis. Solución encontrada con PuLP (CBC Solver).")
    print("=" * 65)