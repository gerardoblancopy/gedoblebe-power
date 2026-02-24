/**
 * DC OPF Simulator API Client
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Bus {
  id: number;
  name?: string;
  type: number;
  v_mag: number;
  v_ang: number;
  g_shunt?: number;
  b_shunt?: number;
  base_kv: number;
  zone: number;
  pd?: number;
  qd?: number;
}

export interface Generator {
  id?: string;
  bus: number;
  pg: number;
  qg: number;
  vg: number;
  mbase: number;
  pmax: number;
  pmin: number;
  qmax: number;
  qmin: number;
  cost: number[];
  status?: number;
  name?: string;
}

export interface Line {
  from_bus: number;
  to_bus: number;
  r: number;
  x: number;
  b: number;
  rate_a: number;
  rate_b?: number;
  rate_c?: number;
  status?: number;
}

export interface Load {
  bus: number;
  pd: number;
  qd: number;
}

export interface PowerSystem {
  buses: Bus[];
  generators: Generator[];
  lines: Line[];
  loads: Load[];
  base_mva?: number;
}

export interface CaseData extends PowerSystem { }

export interface GeneratorResult {
  id?: string;
  bus: number;
  pg: number;
  qg: number;
  cost: number;
}

export interface BusResult {
  bus: number;
  va: number;
  vm: number;
  pl: number;
  ql: number;
  marginal_cost: number;
  curtailment: number;
}

export interface LineResult {
  from_bus: number;
  to_bus: number;
  flow_mw: number;
  flow_mvar: number;
  loading_percent: number;
  congestion_rent: number;
}

export interface OPFResult {
  status: string;
  total_cost: number;
  generator_results: GeneratorResult[];
  bus_results: BusResult[];
  line_results: LineResult[];
  objective_value: number;
  total_curtailment: number;
  iterations: number;
}

export async function loadCase(system: PowerSystem): Promise<CaseData> {
  const response = await fetch(`${API_BASE_URL}/case`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(system),
  });
  if (!response.ok) throw new Error('Failed to load case');
  return response.json();
}

export async function loadMatpowerCase(text: string): Promise<CaseData> {
  const response = await fetch(`${API_BASE_URL}/case/text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: text,
  });
  if (!response.ok) throw new Error('Failed to parse MATPOWER case');
  return response.json();
}

export async function getCase(): Promise<CaseData> {
  const response = await fetch(`${API_BASE_URL}/case`);
  if (!response.ok) throw new Error('No case loaded');
  return response.json();
}

export async function runOPF(system?: PowerSystem, enforceLineLimits: boolean = true, voll: number = 10000, removeIsolated: boolean = false): Promise<OPFResult> {
  const response = await fetch(`${API_BASE_URL}/opf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: system ? JSON.stringify({
      case_data: system,
      enforce_line_limits: enforceLineLimits,
      voll: voll,
      remove_isolated: removeIsolated
    }) : JSON.stringify({
      enforce_line_limits: enforceLineLimits,
      voll: voll,
      remove_isolated: removeIsolated
    }),
  });
  if (!response.ok) throw new Error('Failed to run OPF');
  return response.json();
}

export async function getResults(): Promise<OPFResult> {
  const response = await fetch(`${API_BASE_URL}/results`);
  if (!response.ok) throw new Error('No results available');
  return response.json();
}

export async function getExampleCase9(): Promise<PowerSystem> {
  const response = await fetch(`${API_BASE_URL}/example/case9`);
  if (!response.ok) throw new Error('Failed to get example case');
  return response.json();
}

export async function getMatpowerExample(): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/example/matpower`);
  if (!response.ok) throw new Error('Failed to get MATPOWER example');
  return response.text();
}

export async function exportCSV(): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/export/csv`);
  if (!response.ok) throw new Error('Failed to export CSV');
  return response.blob();
}

export async function exportJSON(): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/export/json`);
  if (!response.ok) throw new Error('Failed to export JSON');
  return response.blob();
}

export function triggerExport(format: 'csv' | 'json') {
  const url = `${API_BASE_URL}/export/${format}`;
  // Using target='_blank' helps Chrome handle the download as a navigation event
  // without replacing the current page context, often bypassing strict click checks.

  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  a.target = '_blank';

  document.body.appendChild(a);
  a.click();

  // Increase timeout to 2s to ensure browser registers the action
  setTimeout(() => {
    document.body.removeChild(a);
  }, 2000);
}
export async function getAvailableCases(): Promise<string[]> {
  const response = await fetch(`${API_BASE_URL}/cases`);
  if (!response.ok) throw new Error('Failed to list cases');
  return response.json();
}

export async function loadServerCase(filename: string): Promise<CaseData> {
  const response = await fetch(`${API_BASE_URL}/cases/${filename}/load`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to load case');
  return response.json();
}

export async function saveServerCase(filename: string, system: PowerSystem): Promise<{ status: string, message: string, filename: string }> {
  const response = await fetch(`${API_BASE_URL}/cases/${filename}/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(system),
  });
  if (!response.ok) throw new Error('Failed to save case to server');
  return response.json();
}

export function downloadBlob(blob: Blob, filename: string) {
  // Create object URL
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  a.setAttribute('download', filename);

  document.body.appendChild(a);
  a.click();

  // Delay cleanup to ensure download starts
  setTimeout(() => {
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }, 100);
}
