/**
 * Global state management with Zustand
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { PowerSystem, OPFResult, Bus, Generator, Line, Load } from './api';

interface PowerSystemState {
  // Power system data
  buses: Bus[];
  generators: Generator[];
  lines: Line[];
  loads: Load[];
  baseMVA: number;

  // OPF results
  results: OPFResult | null;

  // UI state
  selectedBus: number | null;
  selectedGenerator: number | null;
  selectedLine: number | null;
  isSolving: boolean;
  error: string | null;

  // Actions
  setSystem: (system: PowerSystem) => void;
  addBus: (bus: Bus) => void;
  updateBus: (id: number, updates: Partial<Bus>) => void;
  removeBus: (id: number) => void;
  addGenerator: (gen: Generator) => void;
  updateGenerator: (bus: number, updates: Partial<Generator>) => void;
  removeGenerator: (bus: number) => void;
  addLine: (line: Line) => void;
  updateLine: (index: number, updates: Partial<Line>) => void;
  removeLine: (index: number) => void;
  addLoad: (load: Load) => void;
  updateLoad: (bus: number, updates: Partial<Load>) => void;
  removeLoad: (bus: number) => void;
  setResults: (results: OPFResult | null) => void;
  setSelectedBus: (id: number | null) => void;
  setSelectedGenerator: (bus: number | null) => void;
  setSelectedLine: (index: number | null) => void;
  setIsSolving: (solving: boolean) => void;
  setError: (error: string | null) => void;
  clearSystem: () => void;
}

export const usePowerSystemStore = create<PowerSystemState>()(
  persist(
    (set, get) => ({
      // Initial state
      buses: [],
      generators: [],
      lines: [],
      loads: [],
      baseMVA: 100,
      results: null,
      selectedBus: null,
      selectedGenerator: null,
      selectedLine: null,
      isSolving: false,
      error: null,

      // Actions
      setSystem: (system) => set({
        buses: system.buses || [],
        generators: system.generators || [],
        lines: system.lines || [],
        loads: system.loads || [],
        baseMVA: system.base_mva || 100,
        results: null,
        error: null,
      }),

      addBus: (bus) => set((state) => ({
        buses: [...state.buses, bus],
      })),

      updateBus: (id, updates) => set((state) => ({
        buses: state.buses.map((b) => b.id === id ? { ...b, ...updates } : b),
      })),

      removeBus: (id) => set((state) => ({
        buses: state.buses.filter((b) => b.id !== id),
        lines: state.lines.filter((l) => l.from_bus !== id && l.to_bus !== id),
        loads: state.loads.filter((l) => l.bus !== id),
        generators: state.generators.filter((g) => g.bus !== id),
      })),

      addGenerator: (gen) => set((state) => ({
        generators: [...state.generators, gen],
      })),

      updateGenerator: (bus, updates) => set((state) => ({
        generators: state.generators.map((g) =>
          g.bus === bus ? { ...g, ...updates } : g
        ),
      })),

      removeGenerator: (bus) => set((state) => ({
        generators: state.generators.filter((g) => g.bus !== bus),
      })),

      addLine: (line) => set((state) => ({
        lines: [...state.lines, line],
      })),

      updateLine: (index, updates) => set((state) => ({
        lines: state.lines.map((l, i) => i === index ? { ...l, ...updates } : l),
      })),

      removeLine: (index) => set((state) => ({
        lines: state.lines.filter((_, i) => i !== index),
      })),

      addLoad: (load) => set((state) => {
        // Remove existing load at same bus
        const filteredLoads = state.loads.filter((l) => l.bus !== load.bus);
        return { loads: [...filteredLoads, load] };
      }),

      updateLoad: (bus, updates) => set((state) => ({
        loads: state.loads.map((l) =>
          l.bus === bus ? { ...l, ...updates } : l
        ),
      })),

      removeLoad: (bus) => set((state) => ({
        loads: state.loads.filter((l) => l.bus !== bus),
      })),

      setResults: (results) => set({ results }),

      setSelectedBus: (id) => set({ selectedBus: id, selectedGenerator: null, selectedLine: null }),
      setSelectedGenerator: (bus) => set({ selectedGenerator: bus, selectedBus: null, selectedLine: null }),
      setSelectedLine: (index) => set({ selectedLine: index, selectedBus: null, selectedGenerator: null }),

      setIsSolving: (solving) => set({ isSolving: solving }),
      setError: (error) => set({ error }),

      clearSystem: () => set({
        buses: [],
        generators: [],
        lines: [],
        loads: [],
        baseMVA: 100,
        results: null,
        error: null,
      }),
    }),
    {
      name: 'dc-opf-storage',
      partialize: (state) => ({
        buses: state.buses,
        generators: state.generators,
        lines: state.lines,
        loads: state.loads,
        baseMVA: state.baseMVA,
      }),
    }
  )
);
