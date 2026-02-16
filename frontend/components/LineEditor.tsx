'use client';

import { useState, useEffect } from 'react';
import { usePowerSystemStore } from '@/lib/store';

interface LineEditorProps {
  lineIndex: number;
}

export default function LineEditor({ lineIndex }: LineEditorProps) {
  const { buses, lines, updateLine, removeLine, setSelectedLine } = usePowerSystemStore();
  const line = lines[lineIndex];
  const fromBus = buses.find(b => b.id === line?.from_bus);
  const toBus = buses.find(b => b.id === line?.to_bus);
  const fromLabel = fromBus?.name || `Bus ${line?.from_bus}`;
  const toLabel = toBus?.name || `Bus ${line?.to_bus}`;
  const [localLine, setLocalLine] = useState(line);

  useEffect(() => {
    setLocalLine(line);
  }, [line]);

  if (!line) return null;

  const handleUpdate = (updated: typeof localLine) => {
    if (updated) {
      setLocalLine(updated);
      updateLine(lineIndex, updated);
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Line {fromLabel} → {toLabel}</span>
        <button className="icon-btn" onClick={() => setSelectedLine(null)}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">From Bus</label>
          <input
            type="number"
            className="form-input"
            value={localLine?.from_bus || ''}
            disabled
          />
        </div>
        <div className="form-group">
          <label className="form-label">To Bus</label>
          <input
            type="number"
            className="form-input"
            value={localLine?.to_bus || ''}
            disabled
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Resistance (pu)</label>
          <input
            type="number"
            className="form-input"
            value={localLine?.r || 0}
            step="0.001"
            onChange={(e) => {
              const updated = { ...localLine!, r: Number(e.target.value) };
              handleUpdate(updated);
            }}
          />
        </div>
        <div className="form-group">
          <label className="form-label">Reactance (pu)</label>
          <input
            type="number"
            className="form-input"
            value={localLine?.x || 0.1}
            step="0.001"
            onChange={(e) => {
              const updated = { ...localLine!, x: Number(e.target.value) };
              handleUpdate(updated);
            }}
          />
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">Susceptance (pu)</label>
        <input
          type="number"
          className="form-input"
          value={localLine?.b || 0}
          step="0.001"
          onChange={(e) => {
            const updated = { ...localLine!, b: Number(e.target.value) };
            handleUpdate(updated);
          }}
        />
      </div>

      <hr style={{ margin: '1rem 0', border: 'none', borderTop: '1px solid #2e3348' }} />

      <div className="form-group">
        <label className="form-label">Rating (MW)</label>
        <input
          type="number"
          className="form-input"
          value={localLine?.rate_a || 250}
          onChange={(e) => {
            const updated = { ...localLine!, rate_a: Number(e.target.value) };
            handleUpdate(updated);
          }}
        />
      </div>

      <div className="btn-group">
        <button
          className="btn btn-danger"
          onClick={() => {
            removeLine(lineIndex);
            setSelectedLine(null);
          }}
        >
          Delete Line
        </button>
      </div>
    </div>
  );
}
