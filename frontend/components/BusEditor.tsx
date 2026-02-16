'use client';

import { useState, useEffect } from 'react';
import { usePowerSystemStore } from '@/lib/store';

interface BusEditorProps {
  busId: number;
}

export default function BusEditor({ busId }: BusEditorProps) {
  const { buses, generators, loads, updateBus, removeBus, addGenerator, addLoad, setSelectedBus } = usePowerSystemStore();

  const bus = buses.find((b) => b.id === busId);
  const generator = generators.find((g) => g.bus === busId);
  const load = loads.find((l) => l.bus === busId);

  const [localBus, setLocalBus] = useState(bus);
  const [hasGen, setHasGen] = useState(!!generator);
  const [hasLoad, setHasLoad] = useState(!!load);
  const [genCost, setGenCost] = useState(generator?.cost[1] || 25);
  const [genPmax, setGenPmax] = useState(generator?.pmax || 250);
  const [loadPd, setLoadPd] = useState(load?.pd || 0);
  const [loadQd, setLoadQd] = useState(load?.qd || 0);

  useEffect(() => {
    setLocalBus(bus);
    setHasGen(!!generator);
    setHasLoad(!!load);
    setGenCost(generator?.cost[1] || 25);
    setGenPmax(generator?.pmax || 250);
    setLoadPd(load?.pd || 0);
    setLoadQd(load?.qd || 0);
  }, [busId]);

  if (!bus) return null;

  const handleUpdateBus = () => {
    if (localBus) {
      updateBus(busId, localBus);
    }
  };

  const handleAddGenerator = () => {
    if (!hasGen) {
      addGenerator({
        bus: busId,
        pg: 0,
        qg: 0,
        vg: 1.0,
        mbase: 100,
        pmax: genPmax,
        pmin: 10,
        qmax: 300,
        qmin: -300,
        cost: [0, genCost, 0],
      });
      setHasGen(true);
    }
  };

  const handleRemoveGenerator = () => {
    if (hasGen) {
      usePowerSystemStore.getState().removeGenerator(busId);
      setHasGen(false);
    }
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

      <hr style={{ margin: '1rem 0', border: 'none', borderTop: '1px solid #2e3348' }} />

      <div className="form-group">
        <label className="form-label">
          <input
            type="checkbox"
            checked={hasGen}
            onChange={(e) => e.target.checked ? handleAddGenerator() : handleRemoveGenerator()}
            style={{ marginRight: '0.5rem' }}
          />
          Has Generator
        </label>
        {hasGen && (
          <div style={{ marginTop: '0.5rem' }}>
            <div className="form-row" style={{ marginBottom: '0.5rem' }}>
              <div>
                <label className="form-label">a ($/MW²h)</label>
                <input
                  type="number"
                  className="form-input"
                  value={generator?.cost[0] ?? 0}
                  step="0.01"
                  onChange={(e) => {
                    const newCost = [...(generator?.cost || [0, 25, 0])];
                    newCost[0] = Number(e.target.value);
                    usePowerSystemStore.getState().updateGenerator(busId, { cost: newCost });
                  }}
                />
              </div>
              <div>
                <label className="form-label">b ($/MWh)</label>
                <input
                  type="number"
                  className="form-input"
                  value={generator?.cost[1] ?? 25}
                  onChange={(e) => {
                    const newCost = [...(generator?.cost || [0, 25, 0])];
                    newCost[1] = Number(e.target.value);
                    usePowerSystemStore.getState().updateGenerator(busId, { cost: newCost });
                  }}
                />
              </div>
              <div>
                <label className="form-label">c ($/h)</label>
                <input
                  type="number"
                  className="form-input"
                  value={generator?.cost[2] ?? 0}
                  onChange={(e) => {
                    const newCost = [...(generator?.cost || [0, 25, 0])];
                    newCost[2] = Number(e.target.value);
                    usePowerSystemStore.getState().updateGenerator(busId, { cost: newCost });
                  }}
                />
              </div>
            </div>
            <div className="form-row">
              <div>
                <label className="form-label">Pmax (MW)</label>
                <input
                  type="number"
                  className="form-input"
                  value={generator?.pmax ?? 250}
                  onChange={(e) => {
                    usePowerSystemStore.getState().updateGenerator(busId, {
                      pmax: Number(e.target.value),
                    });
                  }}
                />
              </div>
              <div>
                <label className="form-label">Pmin (MW)</label>
                <input
                  type="number"
                  className="form-input"
                  value={generator?.pmin ?? 0}
                  onChange={(e) => {
                    usePowerSystemStore.getState().updateGenerator(busId, {
                      pmin: Number(e.target.value),
                    });
                  }}
                />
              </div>
            </div>
          </div>
        )}
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
