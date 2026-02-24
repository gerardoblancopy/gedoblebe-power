'use client';

import { useState, useEffect } from 'react';
import { usePowerSystemStore } from '@/lib/store';
import { Generator } from '@/lib/api';

interface GeneratorEditorProps {
  genId: string;
}

export default function GeneratorEditor({ genId }: GeneratorEditorProps) {
  const { buses, generators, updateGenerator, removeGenerator, setSelectedGenerator } = usePowerSystemStore();
  const generator = generators.find((g) => g.id === genId);
  const busData = buses.find(b => b.id === generator?.bus);
  const busLabel = busData?.name || `Bus ${generator?.bus}`;
  const [localGen, setLocalGen] = useState(generator);

  useEffect(() => {
    setLocalGen(generator);
  }, [generator]);

  if (!generator) return null;

  const handleUpdate = (updates: Partial<Generator>) => {
    if (generator) {
      updateGenerator(genId, updates);
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Edit Generator {generator.name ? ` — ${generator.name}` : `(Bus ${generator.bus})`}</span>
        <button className="icon-btn" onClick={() => setSelectedGenerator(null)}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <div className="form-group">
        <label className="form-label">Generator Name</label>
        <input
          type="text"
          className="form-input"
          placeholder="e.g. Unit 1"
          value={generator.name || ''}
          onChange={(e) => updateGenerator(genId, { name: e.target.value })}
        />
      </div>

      <div className="form-group" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', background: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: '8px' }}>
        <div>
          <label className="form-label" style={{ marginBottom: 2 }}>In Service</label>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {localGen?.status !== 0 ? 'Connected to grid' : 'Disconnected'}
          </span>
        </div>
        <label className="switch">
          <input
            type="checkbox"
            className="toggle-input"
            checked={localGen?.status !== 0}
            onChange={(e) => {
              const newStatus = e.target.checked ? 1 : 0;
              setLocalGen({ ...localGen!, status: newStatus });
              handleUpdate({ status: newStatus });
            }}
          />
          <span className="slider round"></span>
        </label>
      </div>

      <div className="form-group">
        <label className="form-label">Cost Coefficients</label>
        <div className="form-row">
          <div>
            <label className="form-label">a ($/MW²h)</label>
            <input
              type="number"
              className="form-input"
              value={localGen?.cost[0] ?? 0}
              step="0.01"
              onChange={(e) => {
                const newCost = [...(localGen?.cost || [0, 25, 0])];
                newCost[0] = Number(e.target.value);
                setLocalGen({ ...localGen!, cost: newCost });
                handleUpdate({ cost: newCost });
              }}
            />
          </div>
          <div>
            <label className="form-label">b ($/MWh)</label>
            <input
              type="number"
              className="form-input"
              value={localGen?.cost[1] ?? 25}
              step="1"
              onChange={(e) => {
                const newCost = [...(localGen?.cost || [0, 25, 0])];
                newCost[1] = Number(e.target.value);
                setLocalGen({ ...localGen!, cost: newCost });
                handleUpdate({ cost: newCost });
              }}
            />
          </div>
          <div>
            <label className="form-label">c ($/h)</label>
            <input
              type="number"
              className="form-input"
              value={localGen?.cost[2] ?? 0}
              step="1"
              onChange={(e) => {
                const newCost = [...(localGen?.cost || [0, 25, 0])];
                newCost[2] = Number(e.target.value);
                setLocalGen({ ...localGen!, cost: newCost });
                handleUpdate({ cost: newCost });
              }}
            />
          </div>
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Pmin (MW)</label>
          <input
            type="number"
            className="form-input"
            value={localGen?.pmin ?? 0}
            onChange={(e) => {
              const pmin = Number(e.target.value);
              setLocalGen({ ...localGen!, pmin });
              handleUpdate({ pmin });
            }}
          />
        </div>
        <div className="form-group">
          <label className="form-label">Pmax (MW)</label>
          <input
            type="number"
            className="form-input"
            value={localGen?.pmax ?? 250}
            onChange={(e) => {
              const pmax = Number(e.target.value);
              setLocalGen({ ...localGen!, pmax });
              handleUpdate({ pmax });
            }}
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Qmin (MVAR)</label>
          <input
            type="number"
            className="form-input"
            value={localGen?.qmin ?? -300}
            onChange={(e) => {
              const qmin = Number(e.target.value);
              setLocalGen({ ...localGen!, qmin });
              handleUpdate({ qmin });
            }}
          />
        </div>
        <div className="form-group">
          <label className="form-label">Qmax (MVAR)</label>
          <input
            type="number"
            className="form-input"
            value={localGen?.qmax ?? 300}
            onChange={(e) => {
              const qmax = Number(e.target.value);
              setLocalGen({ ...localGen!, qmax });
              handleUpdate({ qmax });
            }}
          />
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">Voltage Setpoint (pu)</label>
        <input
          type="number"
          className="form-input"
          value={localGen?.vg || 1.0}
          step="0.01"
          onChange={(e) => {
            const vg = Number(e.target.value);
            setLocalGen({ ...localGen!, vg });
            handleUpdate({ vg });
          }}
        />
      </div>

      <div className="btn-group">
        <button
          className="btn btn-danger"
          onClick={() => {
            removeGenerator(genId);
            setSelectedGenerator(null);
          }}
        >
          Remove Generator
        </button>
      </div>
    </div>
  );
}
