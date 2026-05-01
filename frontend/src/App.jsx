import React, { useState, useMemo } from 'react';
import { Play, Wallet, Box, CheckCircle2, BarChart3, PieChart as PieIcon, Cpu } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';

function App() {
  const [budget, setBudget] = useState(850000);
  const [tdp, setTdp] = useState(12000);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleOptimize = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ budget: Number(budget), tdp: Number(tdp) })
      });
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error("Error conectando con el servidor Python:", error);
    }
    setLoading(false);
  };

  const categoryColors = {
    "Servidor": "#1B6CA8",
    "GPU/IA": "#C0392B",
    "Storage": "#27AE60",
    "Network": "#8E44AD",
    "Security": "#E67E22",
    "Admin": "#7F8C8D"
  };

  const donutData = useMemo(() => {
    if (!results) {
      return [];
    }
    const tdpMap = results.selected_items.reduce((acc, item) => {
      acc[item.categoria] = (acc[item.categoria] || 0) + item.TDP_W;
      return acc;
    }, {});
    return Object.keys(tdpMap).map(key => ({ name: key, value: tdpMap[key], color: categoryColors[key] }));
  }, [results]);

  return (
    <div style={{ backgroundColor: '#020617', minHeight: '100vh', color: '#f1f5f9', padding: '2rem', fontFamily: 'sans-serif' }}>
      <header style={{ borderBottom: '1px solid #1e293b', paddingBottom: '1rem', marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2.25rem', fontWeight: '900', color: '#22d3ee', margin: 0 }}>
          NorthGrid Colocation
        </h1>
        <p style={{ color: '#94a3b8', margin: '0.5rem 0 0 0' }}>PIA Investigación de Operaciones 2026 - Optimización de Rack</p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
        <div style={{ backgroundColor: '#0f172a', padding: '1.5rem', borderRadius: '1rem', border: '1px solid #1e293b', height: 'fit-content' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#22d3ee', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
            <Wallet size={20}/> Restricciones del Caso
          </h2>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.75rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 'bold', marginBottom: '0.5rem' }}>Presupuesto CAPEX</label>
            <input type="range" min="300000" max="1500000" step="10000" value={budget} onChange={(e) => setBudget(e.target.value)} style={{ width: '100%' }} />
            <p style={{ fontSize: '1.25rem', fontFamily: 'monospace', color: '#22d3ee', fontWeight: 'bold', margin: '0.5rem 0 0 0' }}>${Number(budget).toLocaleString()}</p>
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <label style={{ display: 'block', fontSize: '0.75rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 'bold', marginBottom: '0.5rem' }}>Límite Térmico (TDP)</label>
            <input type="range" min="2000" max="15000" step="100" value={tdp} onChange={(e) => setTdp(e.target.value)} style={{ width: '100%' }} />
            <p style={{ fontSize: '1.25rem', fontFamily: 'monospace', color: '#f97316', fontWeight: 'bold', margin: '0.5rem 0 0 0' }}>{tdp} W</p>
          </div>

          <button onClick={handleOptimize} disabled={loading} style={{ width: '100%', padding: '1rem', backgroundColor: '#0891b2', color: 'white', borderRadius: '0.5rem', fontWeight: 'bold', textTransform: 'uppercase', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem', border: 'none', cursor: 'pointer' }}>
            {loading ? "Calculando..." : <><Play size={18}/> Ejecutar Solver</>}
          </button>

          {results && (
            <div style={{ marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid #1e293b', textAlign: 'center' }}>
              <p style={{ color: '#94a3b8', fontSize: '0.75rem', textTransform: 'uppercase', fontWeight: 'bold', margin: 0 }}>Valor Operativo Total</p>
              <p style={{ fontSize: '3rem', fontWeight: '900', margin: '0.5rem 0' }}>{results.total_svo}</p>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', padding: '0.25rem 0.75rem', backgroundColor: 'rgba(34, 197, 94, 0.1)', color: '#4ade80', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 'bold', border: '1px solid rgba(34, 197, 94, 0.2)' }}>
                <CheckCircle2 size={12}/> {results.status}
              </span>
            </div>
          )}
        </div>
        <div style={{ gridColumn: 'span 2' }}>
          {results ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>

              {/* Gráfica 1: SVO (Barras) */}
              <div style={{ backgroundColor: '#0f172a', padding: '1.25rem', borderRadius: '1rem', border: '1px solid #1e293b' }}>
                <h3 style={{ fontSize: '0.875rem', fontWeight: 'bold', color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: '0.5rem', margin: '0 0 1rem 0' }}><BarChart3 size={16}/> SVO por Componente</h3>
                <div style={{ height: '300px', width: '100%' }}>
                  <ResponsiveContainer>
                    <BarChart layout="vertical" data={results.selected_items} margin={{ left: -10, right: 10, bottom: 0, top: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#1e293b" />
                      <XAxis type="number" stroke="#64748b" fontSize={10} />
                      <YAxis dataKey="nombre" type="category" width={100} stroke="#64748b" fontSize={9} tickFormatter={(val) => val.substring(0, 12) + "..."} />
                      <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', fontSize: '11px' }} />
                      <Bar dataKey="SVO" radius={[0, 4, 4, 0]} barSize={10}>
                        {results.selected_items.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={categoryColors[entry.categoria] || "#22d3ee"} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Gráfica 2: TDP (Dona) */}
              <div style={{ backgroundColor: '#0f172a', padding: '1.25rem', borderRadius: '1rem', border: '1px solid #1e293b' }}>
                <h3 style={{ fontSize: '0.875rem', fontWeight: 'bold', color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: '0.5rem', margin: '0 0 1rem 0' }}><PieIcon size={16}/> TDP por Categoría</h3>
                <div style={{ height: '300px', width: '100%' }}>
                  <ResponsiveContainer>
                    <PieChart>
                      <Pie data={donutData} innerRadius={60} outerRadius={80} paddingAngle={2} dataKey="value" stroke="none">
                        {donutData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => `${value} W`} contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', fontSize: '11px' }} />
                      <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{ fontSize: '10px', color: '#94a3b8' }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Gráfica 3: Utilización de Recursos */}
              <div style={{ backgroundColor: '#0f172a', padding: '1.5rem', borderRadius: '1rem', border: '1px solid #1e293b', gridColumn: '1 / -1' }}>
                <h3 style={{ fontSize: '0.875rem', fontWeight: 'bold', color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: '0.5rem', margin: '0 0 1.5rem 0' }}><Cpu size={16}/> Utilización de Capacidad Disponible</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

                  {/* Presupuesto */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>
                      <span style={{ color: '#22d3ee' }}>Presupuesto CAPEX</span>
                      <span style={{ color: '#94a3b8' }}>${results.usage.cost.toLocaleString()} / ${Number(budget).toLocaleString()}</span>
                    </div>
                    <div style={{ width: '100%', backgroundColor: '#1e293b', borderRadius: '9999px', height: '12px', overflow: 'hidden' }}>
                      <div style={{ backgroundColor: '#06b6d4', height: '100%', width: `${Math.min((results.usage.cost / budget) * 100, 100)}%`, transition: 'width 0.5s ease' }}></div>
                    </div>
                  </div>

                  {/* Térmico */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>
                      <span style={{ color: '#f97316' }}>Límite Térmico (W)</span>
                      <span style={{ color: '#94a3b8' }}>{results.usage.tdp.toLocaleString()} W / {Number(tdp).toLocaleString()} W</span>
                    </div>
                    <div style={{ width: '100%', backgroundColor: '#1e293b', borderRadius: '9999px', height: '12px', overflow: 'hidden' }}>
                      <div style={{ backgroundColor: '#f97316', height: '100%', width: `${Math.min((results.usage.tdp / tdp) * 100, 100)}%`, transition: 'width 0.5s ease' }}></div>
                    </div>
                  </div>

                  {/* Espacio */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>
                      <span style={{ color: '#34d399' }}>Espacio en Rack (U)</span>
                      <span style={{ color: '#94a3b8' }}>{results.usage.u} U / 42 U</span>
                    </div>
                    <div style={{ width: '100%', backgroundColor: '#1e293b', borderRadius: '9999px', height: '12px', overflow: 'hidden' }}>
                      <div style={{ backgroundColor: '#10b981', height: '100%', width: `${Math.min((results.usage.u / 42) * 100, 100)}%`, transition: 'width 0.5s ease' }}></div>
                    </div>
                  </div>

                </div>
              </div>

            </div>
          ) : (
            <div style={{ height: '400px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', border: '2px dashed #1e293b', borderRadius: '1rem', backgroundColor: 'rgba(15, 23, 42, 0.5)', color: '#64748b', padding: '2rem', textAlign: 'center' }}>
              <Box size={48} style={{ opacity: 0.5, color: '#06b6d4', marginBottom: '1rem' }} />
              <p style={{ fontSize: '0.875rem', fontStyle: 'italic', maxWidth: '300px' }}>El panel está listo. Ajusta el presupuesto y el límite térmico, luego ejecuta el modelo.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;