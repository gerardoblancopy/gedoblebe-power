'use client';

import { useState, useEffect } from 'react';
import { usePowerSystemStore } from '@/lib/store';

interface GeneratorEditorProps {
  bus: number;
}

export default function GeneratorEditor({ bus }: GeneratorEditorProps) {
  const { buses, generators, updateGenerator, removeGenerator, setSelectedGenerator } = usePowerSystemStore();
  const busData = buses.find(b => b.id === bus);
  const busLabel = busData?.name || `Bus ${bus}`;

  const generator = generators.find((g) => g.bus === bus);
  const [localGen, setLocalGen] = useState(generator);

  useEffect(() => {
    setLocalGen(generator);
  }, [generator]);

  if (!generator) return null;

  const handleUpdate = () => {
    if (localGen) {
      updateGenerator(bus, localGen);
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Generator @ {busLabel}</span>
        <button className="icon-btn" onClick={() => setSelectedGenerator(null)}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
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
                handleUpdate();
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
                handleUpdate();
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
                handleUpdate();
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
              setLocalGen({ ...localGen!, pmin: Number(e.target.value) });
              handleUpdate();
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
              setLocalGen({ ...localGen!, pmax: Number(e.target.value) });
              handleUpdate();
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
              setLocalGen({ ...localGen!, qmin: Number(e.target.value) });
              handleUpdate();
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
              setLocalGen({ ...localGen!, qmax: Number(e.target.value) });
              handleUpdate();
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
            setLocalGen({ ...localGen!, vg: Number(e.target.value) });
            handleUpdate();
          }}
        />
      </div>

      <div className="btn-group">
        <button
          className="btn btn-danger"
          onClick={() => {
            removeGenerator(bus);
            setSelectedGenerator(null);
          }}
        >
          Remove Generator
        </button>
      </div>
    </div>
  );
}
