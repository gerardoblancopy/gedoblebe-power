'use client';

import { useState, useEffect } from 'react';
import { usePowerSystemStore } from '@/lib/store';

interface BusEditorProps {
  busId: number;
}

export default function BusEditor({ busId }: BusEditorProps) {
  const { buses, generators, loads, updateBus, removeBus, addGenerator, addLoad, setSelectedBus } = usePowerSystemStore();

  const bus = buses.find((b) => b.id === busId);
  const busGenerators = generators.filter((g) => g.bus === busId);
  const load = loads.find((l) => l.bus === busId);

  const [localBus, setLocalBus] = useState(bus);
  const [hasLoad, setHasLoad] = useState(!!load);
  const [loadPd, setLoadPd] = useState(load?.pd || 0);
  const [loadQd, setLoadQd] = useState(load?.qd || 0);

  useEffect(() => {
    setLocalBus(bus);
    setHasLoad(!!load);
    setLoadPd(load?.pd || 0);
    setLoadQd(load?.qd || 0);
  }, [busId, bus, load]);

  if (!bus) return null;

  const handleUpdateBus = () => {
    if (localBus) {
      updateBus(busId, localBus);
    }
  };

  const handleAddGenerator = () => {
    addGenerator({
      bus: busId,
      pg: 0,
      qg: 0,
      vg: 1.0,
      mbase: 100,
      pmax: 250,
      pmin: 0,
      qmax: 300,
      qmin: -300,
      cost: [0, 25, 0],
      status: 1
    });
  };

  const handleAddLoad = () => {
    if (!hasLoad) {
      const pd = loadPd > 0 ? loadPd : 100;
      setLoadPd(pd);
      addLoad({ bus: busId, pd, qd: loadQd });
      setHasLoad(true);
    }
  };

  const handleRemoveLoad = () => {
    if (hasLoad) {
      usePowerSystemStore.getState().removeLoad(busId);
      setHasLoad(false);
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Edit Bus {busId}{localBus?.name ? ` — ${localBus.name}` : ''}</span>
        <button className="icon-btn" onClick={() => setSelectedBus(null)}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <div className="form-group">
        <label className="form-label">Bus Name</label>
        <input
          type="text"
          className="form-input"
          placeholder={`Bus ${busId}`}
          value={localBus?.name || ''}
          onChange={(e) => {
            const updated = { ...localBus!, name: e.target.value || undefined };
            setLocalBus(updated);
            updateBus(busId, updated);
          }}
        />
      </div>

      <div className="form-group">
        <label className="form-label">Bus Type</label>
        <select
          className="form-input"
          value={localBus?.type}
          onChange={(e) => {
            setLocalBus({ ...localBus!, type: Number(e.target.value) });
            handleUpdateBus();
          }}
        >
          <option value={1}>PQ (Load Bus)</option>
          <option value={2}>PV (Generator Bus)</option>
          <option value={3}>Slack (Reference)</option>
        </select>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Voltage (pu)</label>
          <input
            type="number"
            className="form-input"
            value={localBus?.v_mag || 1.0}
            step="0.01"
            onChange={(e) => {
              setLocalBus({ ...localBus!, v_mag: Number(e.target.value) });
              handleUpdateBus();
            }}
          />
        </div>
        <div className="form-group">
          <label className="form-label">Base kV</label>
          <input
            type="number"
            className="form-input"
            value={localBus?.base_kv || 345}
            onChange={(e) => {
              setLocalBus({ ...localBus!, base_kv: Number(e.target.value) });
              handleUpdateBus();
            }}
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">G Shunt (pu)</label>
          <input
            type="number"
            className="form-input"
            value={localBus?.g_shunt || 0}
            step="0.001"
            onChange={(e) => {
              setLocalBus({ ...localBus!, g_shunt: Number(e.target.value) });
              handleUpdateBus();
            }}
          />
        </div>
        <div className="form-group">
          <label className="form-label">B Shunt (pu)</label>
          <input
            type="number"
            className="form-input"
            value={localBus?.b_shunt || 0}
            step="0.001"
            onChange={(e) => {
              setLocalBus({ ...localBus!, b_shunt: Number(e.target.value) });
              handleUpdateBus();
            }}
          />
        </div>
      </div>

      <hr style={{ margin: '1rem 0', border: 'none', borderTop: '1px solid #2e3348' }} />

      <div className="form-group">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <label className="form-label" style={{ marginBottom: 0 }}>Generators ({busGenerators.length})</label>
          <button className="btn btn-sm" onClick={handleAddGenerator} style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem' }}>
            + Add Unit
          </button>
        </div>

        <div className="element-list" style={{ background: 'rgba(0,0,0,0.15)', borderRadius: '6px', padding: '0.25rem' }}>
          {busGenerators.map((gen, idx) => (
            <div
              key={gen.id}
              className="element-item"
              style={{ padding: '0.5rem', marginBottom: idx === busGenerators.length - 1 ? 0 : '0.25rem', border: '1px solid rgba(255,255,255,0.05)' }}
              onClick={() => usePowerSystemStore.getState().setSelectedGenerator(gen.id || null)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                <div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{gen.name || `Gen #${idx + 1}`}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {gen.pmax} MW · {gen.cost[1]} $/MWh
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <div className={`status-dot ${gen.status !== 0 ? 'active' : ''}`} />
                  <button
                    className="icon-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (gen.id) usePowerSystemStore.getState().removeGenerator(gen.id);
                    }}
                    style={{ color: '#ef4444' }}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <line x1="18" y1="6" x2="6" y2="18"></line>
                      <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          ))}
          {busGenerators.length === 0 && (
            <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              No production units
            </div>
          )}
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">
          <input
            type="checkbox"
            checked={hasLoad}
            onChange={(e) => e.target.checked ? handleAddLoad() : handleRemoveLoad()}
            style={{ marginRight: '0.5rem' }}
          />
          Has Load
        </label>
        {hasLoad && (
          <div style={{ marginTop: '0.5rem' }}>
            <div className="form-row">
              <div>
                <label className="form-label">P (MW)</label>
                <input
                  type="number"
                  className="form-input"
                  value={loadPd}
                  onChange={(e) => {
                    setLoadPd(Number(e.target.value));
                    if (hasLoad) {
                      usePowerSystemStore.getState().updateLoad(busId, {
                        pd: Number(e.target.value),
                      });
                    }
                  }}
                />
              </div>
              <div>
                <label className="form-label">Q (MVAR)</label>
                <input
                  type="number"
                  className="form-input"
                  value={loadQd}
                  onChange={(e) => {
                    setLoadQd(Number(e.target.value));
                    if (hasLoad) {
                      usePowerSystemStore.getState().updateLoad(busId, {
                        qd: Number(e.target.value),
                      });
                    }
                  }}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="btn-group">
        <button
          className="btn btn-danger"
          onClick={() => {
            removeBus(busId);
            setSelectedBus(null);
          }}
        >
          Delete Bus
        </button>
      </div>
    </div>
  );
}
