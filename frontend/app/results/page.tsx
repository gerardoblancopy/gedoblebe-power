'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { usePowerSystemStore } from '@/lib/store';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Area,
  AreaChart,
} from 'recharts';

/** Format number: 1 decimal, thousands separator */
const fmt = (n: number, decimals = 1) =>
  n.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });

export default function ResultsPage() {
  const pathname = usePathname();
  const { results, buses, generators, lines, loads } = usePowerSystemStore();

  if (!results) {
    return (
      <div className="app">
        <header className="header">
          <h1>Gedoblebe Power Simulator</h1>
          <nav className="header-nav">
            <Link href="/" className={`nav-btn ${pathname === '/' ? 'active' : ''}`}>Editor</Link>
            <Link href="/results" className={`nav-btn ${pathname === '/results' ? 'active' : ''}`}>Results</Link>
          </nav>
        </header>
        <main className="main-content" style={{ justifyContent: 'center', alignItems: 'center' }}>
          <div className="empty-state">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#4b5563" strokeWidth="1.5" style={{ marginBottom: '1rem', opacity: 0.5 }}>
              <path d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3>No Results Available</h3>
            <p>Run DC OPF from the Editor to see results here.</p>
            <Link href="/" className="btn btn-primary" style={{ marginTop: '1rem' }}>Go to Editor</Link>
          </div>
        </main>
      </div>
    );
  }

  // Helper: display bus name or ID
  const busLabel = (id: number) => {
    const bus = buses.find(b => b.id === id);
    return bus?.name || `Bus ${id}`;
  };

  // Derived metrics
  const totalGen = results.generator_results.reduce((s, g) => s + g.pg, 0);
  const totalLoad = loads.reduce((s, l) => s + l.pd, 0);
  const maxLMP = Math.max(...results.bus_results.map(b => b.marginal_cost));
  const minLMP = Math.min(...results.bus_results.map(b => b.marginal_cost));
  const avgLMP = results.bus_results.reduce((s, b) => s + b.marginal_cost, 0) / results.bus_results.length;
  const maxLoading = Math.max(...results.line_results.map(l => l.loading_percent));
  const totalLosses = Math.abs(totalGen - totalLoad);

  // Chart data
  const genData = results.generator_results.map((g) => ({
    name: busLabel(g.bus),
    value: g.pg,
    cost: g.cost,
  }));

  const lmpData = results.bus_results.map((b) => ({
    name: busLabel(b.bus),
    lmp: b.marginal_cost,
    load: b.pl,
  }));

  const lineData = results.line_results.map((l) => ({
    name: `${busLabel(l.from_bus)}→${busLabel(l.to_bus)}`,
    flow: Math.abs(l.flow_mw),
    loading: l.loading_percent,
  }));

  const COLORS = ['#6366f1', '#a78bfa', '#34d399', '#22d3ee', '#fbbf24', '#f87171', '#ec4899'];

  const statusColor = results.status === 'optimal' ? '#34d399' : results.status === 'infeasible' ? '#f87171' : '#fbbf24';
  const statusIcon = results.status === 'optimal' ? '✓' : results.status === 'infeasible' ? '✗' : '⚠';

  return (
    <div className="app">
      <header className="header">
        <h1>Gedoblebe Power Simulator — Results</h1>
        <nav className="header-nav">
          <Link href="/" className={`nav-btn ${pathname === '/' ? 'active' : ''}`}>Editor</Link>
          <Link href="/results" className={`nav-btn ${pathname === '/results' ? 'active' : ''}`}>Results</Link>
        </nav>
      </header>

      <main className="main-content" style={{ flexDirection: 'column', overflow: 'hidden' }}>
        {/* ── KPI Strip ─────────────────────────────────────── */}
        <div className="kpi-strip">
          <div className="kpi-card kpi-accent-indigo">
            <div className="kpi-icon" style={{ background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8' }}>⚡</div>
            <div className="kpi-info">
              <span className="kpi-value">${fmt(results.total_cost)}</span>
              <span className="kpi-label">Total Cost ($/h)</span>
            </div>
          </div>
          <div className={`kpi-card ${results.status === 'optimal' ? 'kpi-accent-green' : 'kpi-accent-red'}`}>
            <div className="kpi-icon" style={{ background: statusColor === '#34d399' ? 'rgba(52,211,153,0.15)' : 'rgba(248,113,113,0.15)', color: statusColor }}>
              {statusIcon}
            </div>
            <div className="kpi-info">
              <span className="kpi-value" style={{ color: statusColor, textTransform: 'capitalize' }}>{results.status}</span>
              <span className="kpi-label">Solver Status</span>
            </div>
          </div>
          <div className="kpi-card kpi-accent-purple">
            <div className="kpi-icon" style={{ background: 'rgba(139,92,246,0.15)', color: '#a78bfa' }}>⚙</div>
            <div className="kpi-info">
              <span className="kpi-value">{fmt(totalGen)} <small style={{ fontSize: '0.65rem', color: '#8891a8' }}>MW</small></span>
              <span className="kpi-label">Generation</span>
            </div>
          </div>
          <div className="kpi-card kpi-accent-amber">
            <div className="kpi-icon" style={{ background: 'rgba(249,115,22,0.15)', color: '#fb923c' }}>📊</div>
            <div className="kpi-info">
              <span className="kpi-value">{fmt(totalLoad)} <small style={{ fontSize: '0.65rem', color: '#8891a8' }}>MW</small></span>
              <span className="kpi-label">Demand</span>
            </div>
          </div>
          <div className="kpi-card kpi-accent-cyan">
            <div className="kpi-icon" style={{ background: 'rgba(34,211,238,0.15)', color: '#22d3ee' }}>💲</div>
            <div className="kpi-info">
              <span className="kpi-value">{fmt(avgLMP)} <small style={{ fontSize: '0.65rem', color: '#8891a8' }}>$/MWh</small></span>
              <span className="kpi-label">Avg LMP</span>
            </div>
          </div>
          <div className="kpi-card kpi-accent-rose">
            <div className="kpi-icon" style={{ background: maxLoading > 90 ? 'rgba(248,113,113,0.15)' : 'rgba(52,211,153,0.15)', color: maxLoading > 90 ? '#f87171' : '#34d399' }}>
              {maxLoading > 90 ? '⚠' : '✓'}
            </div>
            <div className="kpi-info">
              <span className="kpi-value" style={{ color: maxLoading > 90 ? '#f87171' : 'inherit' }}>{fmt(maxLoading)}%</span>
              <span className="kpi-label">Peak Loading</span>
            </div>
          </div>
        </div>

        {/* ── Main Grid ────────────────────────────────────── */}
        <div className="results-grid">
          {/* Generator Dispatch — top left */}
          <div className="panel results-panel">
            <div className="panel-header">
              <span className="panel-title">⚡ Generator Dispatch</span>
              <span className="panel-badge">{results.generator_results.length} units</span>
            </div>
            <div style={{ display: 'flex', flex: 1, minHeight: 0, overflow: 'hidden', gap: '0.25rem' }}>
              <div style={{ flex: 1, overflowY: 'auto', minHeight: 0 }}>
                <table className="results-table">
                  <thead>
                    <tr>
                      <th>Bus</th>
                      <th>Pg (MW)</th>
                      <th>Qg (MVAR)</th>
                      <th>Cost ($/h)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.generator_results.map((g) => (
                      <tr key={g.bus}>
                        <td><span className="mono-cell">{busLabel(g.bus)}</span></td>
                        <td className="num-cell">{fmt(g.pg)}</td>
                        <td className="num-cell">{fmt(g.qg)}</td>
                        <td className="num-cell">{fmt(g.cost)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div style={{ width: '140px', flexShrink: 0 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={genData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={25}
                      outerRadius={50}
                      paddingAngle={3}
                      strokeWidth={0}
                    >
                      {genData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value) => `${fmt(Number(value))} MW`}
                      contentStyle={{ background: '#1c1f2e', border: '1px solid #2e3348', borderRadius: '8px', fontSize: '0.75rem' }}
                      itemStyle={{ color: '#edf0f5' }}
                      labelStyle={{ color: '#8891a8' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Bus Results + LMP Chart — top right */}
          <div className="panel results-panel">
            <div className="panel-header">
              <span className="panel-title">🔌 Bus Results & LMP</span>
              <span className="panel-badge">{results.bus_results.length} buses</span>
            </div>
            <div style={{ flex: 1, overflowY: 'auto', minHeight: 0 }}>
              <table className="results-table">
                <thead>
                  <tr>
                    <th>Bus</th>
                    <th>Va (°)</th>
                    <th>Vm (pu)</th>
                    <th>Load</th>
                    <th>LMP</th>
                    <th>Curtail</th>
                  </tr>
                </thead>
                <tbody>
                  {results.bus_results.map((b) => (
                    <tr key={b.bus}>
                      <td><span className="mono-cell">{busLabel(b.bus)}</span></td>
                      <td className="num-cell">{fmt(b.va)}</td>
                      <td className="num-cell">{fmt(b.vm, 3)}</td>
                      <td className="num-cell">{fmt(b.pl)}</td>
                      <td className="num-cell lmp-cell">{fmt(b.marginal_cost)}</td>
                      <td>
                        {(b.curtailment || 0) > 0 ? (
                          <span className="badge badge-danger">{fmt(b.curtailment || 0)}</span>
                        ) : (
                          <span className="badge badge-ok">0.0</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {/* LMP Bar Chart underneath table */}
            <div style={{ height: '80px', flexShrink: 0, marginTop: '0.25rem' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={lmpData} margin={{ top: 2, right: 8, bottom: 0, left: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2e3348" vertical={false} />
                  <XAxis dataKey="name" tick={{ fill: '#8891a8', fontSize: 9 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#8891a8', fontSize: 9 }} axisLine={false} tickLine={false} width={28} tickFormatter={(v) => `$${v}`} />
                  <Tooltip
                    formatter={(value) => `$${fmt(Number(value))} /MWh`}
                    contentStyle={{ background: '#1c1f2e', border: '1px solid #2e3348', borderRadius: '8px', fontSize: '0.75rem' }}
                    itemStyle={{ color: '#edf0f5' }}
                    labelStyle={{ color: '#8891a8' }}
                  />
                  <Bar dataKey="lmp" name="LMP" fill="#a78bfa" radius={[3, 3, 0, 0]} barSize={20} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Line Results — full width bottom */}
          <div className="panel results-panel" style={{ gridColumn: 'span 2' }}>
            <div className="panel-header">
              <span className="panel-title">🔗 Line Flows</span>
              <span className="panel-badge">{results.line_results.length} lines · Max {fmt(maxLoading)}%</span>
            </div>
            <div style={{ flex: 1, overflowY: 'auto', minHeight: 0 }}>
              <table className="results-table">
                <thead>
                  <tr>
                    <th>From</th>
                    <th>To</th>
                    <th>Flow (MW)</th>
                    <th>Loading</th>
                    <th>Cong. Rent</th>
                  </tr>
                </thead>
                <tbody>
                  {results.line_results.map((l, i) => (
                    <tr key={i}>
                      <td><span className="mono-cell">{busLabel(l.from_bus)}</span></td>
                      <td><span className="mono-cell">{busLabel(l.to_bus)}</span></td>
                      <td className="num-cell">{fmt(l.flow_mw)}</td>
                      <td>
                        <div className="loading-bar-container">
                          <div
                            className="loading-bar-fill"
                            style={{
                              width: `${Math.min(l.loading_percent, 100)}%`,
                              background: l.loading_percent > 90 ? '#f87171' : l.loading_percent > 70 ? '#fbbf24' : '#34d399',
                            }}
                          />
                          <span className="loading-bar-text">{fmt(l.loading_percent)}%</span>
                        </div>
                      </td>
                      <td>
                        {Math.abs(l.congestion_rent) > 0.01 ? (
                          <span className="badge badge-warning">${fmt(l.congestion_rent)}</span>
                        ) : (
                          <span className="num-cell" style={{ color: '#636b83' }}>—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
