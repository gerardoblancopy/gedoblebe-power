'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { usePowerSystemStore } from '@/lib/store';
import { forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide, forceX, forceY } from 'd3-force';

interface Point {
  x: number;
  y: number;
}

/** Returns true if segment AB crosses segment CD */
function segmentsIntersect(a: Point, b: Point, c: Point, d: Point): boolean {
  const cross = (o: Point, p: Point, q: Point) =>
    (p.x - o.x) * (q.y - o.y) - (p.y - o.y) * (q.x - o.x);
  const d1 = cross(c, d, a);
  const d2 = cross(c, d, b);
  const d3 = cross(a, b, c);
  const d4 = cross(a, b, d);
  if (((d1 > 0 && d2 < 0) || (d1 < 0 && d2 > 0)) &&
    ((d3 > 0 && d4 < 0) || (d3 < 0 && d4 > 0))) return true;
  return false;
}
export default function NetworkCanvas() {
  const canvasRef = useRef<SVGSVGElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [busPositions, setBusPositions] = useState<Record<number, Point>>({});
  const [dragging, setDragging] = useState<number | null>(null);
  const [mode, setMode] = useState<'select' | 'add-bus' | 'add-line'>('select');
  const [lineStart, setLineStart] = useState<number | null>(null);
  const [mousePos, setMousePos] = useState<Point>({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [panOffset, setPanOffset] = useState<Point>({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const panStartRef = useRef<Point>({ x: 0, y: 0 });
  const panOffsetStartRef = useRef<Point>({ x: 0, y: 0 });

  const {
    buses,
    generators,
    lines,
    loads,
    addBus,
    addLine,
    addGenerator,
    addLoad,
    removeBus,
    removeLine,
    setSelectedBus,
    selectedBus,
    selectedGenerator,
    results,
  } = usePowerSystemStore();

  // Force-directed layout to minimize line crossings
  useEffect(() => {
    if (buses.length === 0 || dimensions.width === 0) return;

    // Check if any bus needs a new position
    const needsLayout = buses.some(b => !busPositions[b.id]);
    if (!needsLayout) return;

    const width = dimensions.width;
    const height = dimensions.height;

    // Create nodes array for D3
    const nodes = buses.map(b => ({
      id: b.id,
      // Retain existing position if available, or initialize near center randomly
      x: busPositions[b.id]?.x || (width / 2 + (Math.random() - 0.5) * 100),
      y: busPositions[b.id]?.y || (height / 2 + (Math.random() - 0.5) * 100),
      busData: b,
    }));

    // Create links array for D3
    const links = lines
      .filter(l => nodes.some(n => n.id === l.from_bus) && nodes.some(n => n.id === l.to_bus))
      .map(l => ({
        source: l.from_bus,
        target: l.to_bus,
      }));

    // If only 1 or 2 buses, skip force simulation and hardcode position
    if (buses.length <= 2) {
      const newPos: Record<number, Point> = {};
      nodes.forEach((n, idx) => {
        newPos[n.id] = {
          x: width / 2 + (idx * 150 - ((buses.length - 1) * 75)),
          y: height / 2
        };
      });
      setBusPositions(newPos);
      return;
    }

    // Set up D3 simulation
    const isLarge = buses.length > 50;

    const simulation = forceSimulation(nodes as any)
      .force(
        "link",
        forceLink(links as any)
          .id((d: any) => d.id)
          .distance(isLarge ? 120 : 200)
      )
      .force("charge", forceManyBody().strength(isLarge ? -1500 : -4000))
      // Collision detection ensures bus icons and their text labels don't overlap
      .force(
        "collide",
        forceCollide().radius((d: any) => {
          const bus = d.busData;
          const label = bus.name || String(bus.id);
          const pillW = Math.max(isLarge ? 20 : 28, label.length * (isLarge ? 6 : 8) + 8);
          // High padding needed to account for vertically stacked labels (LMP, Voltage, Gen/Load)
          return pillW / 2 + 70;
        }).iterations(5)
      )
      .force("x", forceX(width / 2).strength(0.05))
      .force("y", forceY(height / 2).strength(0.05));

    // Run statically
    const ticks = Math.ceil(Math.log(simulation.alphaMin()) / Math.log(1 - simulation.alphaDecay()));
    for (let i = 0; i < ticks; ++i) {
      simulation.tick();
    }

    // Auto-fit to canvas perfectly without needing user to zoom
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    nodes.forEach(n => {
      if (n.x < minX) minX = n.x;
      if (n.x > maxX) maxX = n.x;
      if (n.y < minY) minY = n.y;
      if (n.y > maxY) maxY = n.y;
    });

    const graphW = Math.max(1, maxX - minX);
    const graphH = Math.max(1, maxY - minY);
    const fillMargin = 80; // Margin from edges of canvas

    // Calculate how much we need to scale the graph to fit inside the dimension bounds
    const scaleX = (width - 2 * fillMargin) / graphW;
    const scaleY = (height - 2 * fillMargin) / graphH;
    let finalScale = Math.min(scaleX, scaleY);

    // Limit extreme scaling
    finalScale = Math.max(0.5, Math.min(finalScale, 1.8));

    // Calculate centering offset
    const offsetX = width / 2 - ((maxX + minX) / 2) * finalScale;
    const offsetY = height / 2 - ((maxY + minY) / 2) * finalScale;

    const newPos: Record<number, { x: number; y: number }> = {};
    nodes.forEach(n => {
      newPos[n.id] = {
        x: n.x * finalScale + offsetX,
        y: n.y * finalScale + offsetY
      };
    });

    setBusPositions(newPos);
    setZoom(1); // Ensure we are at 100% zoom to show high LOD text nodes
    setPanOffset({ x: 0, y: 0 }); // reset pan
  }, [buses.length, lines.length, dimensions]);

  // Resize handler
  useEffect(() => {
    const handleResize = () => {
      if (canvasRef.current) {
        const rect = canvasRef.current.parentElement?.getBoundingClientRect();
        if (rect) {
          setDimensions({ width: rect.width, height: rect.height });
        }
      }
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Convert screen coordinates to SVG coordinates (accounts for zoom/viewBox)
  const screenToSvg = useCallback((e: React.MouseEvent): Point => {
    const svg = canvasRef.current;
    if (!svg) return { x: 0, y: 0 };
    const pt = svg.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const ctm = svg.getScreenCTM();
    if (!ctm) return { x: 0, y: 0 };
    const svgPt = pt.matrixTransform(ctm.inverse());
    return { x: svgPt.x, y: svgPt.y };
  }, []);

  const handleCanvasClick = (e: React.MouseEvent<SVGSVGElement>) => {
    if (mode === 'add-bus') {
      const { x, y } = screenToSvg(e);
      if (x || y) {
        const newId = Math.max(0, ...buses.map((b) => b.id)) + 1;
        addBus({
          id: newId,
          type: 1, // PQ bus by default
          v_mag: 1.0,
          v_ang: 0.0,
          base_kv: 345.0,
          zone: 1,
        });
        setBusPositions((prev) => ({ ...prev, [newId]: { x, y } }));
        setMode('select');
      }
    } else if (mode === 'select') {
      setSelectedBus(null);
    }
  };

  const handleBusClick = (busId: number, e: React.MouseEvent) => {
    e.stopPropagation();

    if (mode === 'add-line') {
      if (lineStart === null) {
        setLineStart(busId);
      } else if (lineStart !== busId) {
        // Check if line already exists
        const exists = lines.some(
          (l) =>
            (l.from_bus === lineStart && l.to_bus === busId) ||
            (l.from_bus === busId && l.to_bus === lineStart)
        );
        if (!exists) {
          addLine({
            from_bus: lineStart,
            to_bus: busId,
            r: 0.01,
            x: 0.1,
            b: 0.0,
            rate_a: 250.0,
          });
        }
        setLineStart(null);
        setMode('select');
      }
    } else {
      setSelectedBus(busId);
    }
  };

  const handleBusDrag = (busId: number, e: React.MouseEvent) => {
    if (dragging === busId) {
      const { x, y } = screenToSvg(e as unknown as React.MouseEvent);
      if (x || y) {
        setBusPositions((prev) => ({ ...prev, [busId]: { x, y } }));
      }
    }
  };

  const getBusColor = (type: number) => {
    switch (type) {
      case 3:
        return '#22c55e'; // Slack - green
      case 2:
        return '#3b82f6'; // PV - blue
      default:
        return '#9ca3af'; // PQ - gray
    }
  };

  const getLineWidth = (loading: number) => {
    if (!results) return 2;
    if (loading > 90) return 4;
    if (loading > 70) return 3;
    return 2;
  };

  const getLineColor = (loading: number) => {
    if (!results) return '#636b83';
    if (loading > 90) return '#f87171'; // Red
    if (loading > 70) return '#fbbf24'; // Amber
    return '#34d399'; // Green
  };

  const getLineFlow = (fromBus: number, toBus: number) => {
    if (!results) return null;
    return results.line_results.find(
      (l) =>
        (l.from_bus === fromBus && l.to_bus === toBus) ||
        (l.from_bus === toBus && l.to_bus === fromBus)
    );
  };


  // Get load at a bus
  const getLoadMW = (busId: number): number | null => {
    const load = loads.find((l) => l.bus === busId);
    return load ? load.pd : null;
  };

  // Get curtailment at a bus
  const getCurtailment = (busId: number): number => {
    if (!results) return 0;
    const busResult = results.bus_results.find((b) => b.bus === busId);
    return busResult?.curtailment || 0;
  };

  const busCount = buses.length;
  const isLargeNetwork = busCount > 50;

  // Escalado inverso amortiguado: cuando se hace zoom out (zoom < 1),
  // el texto disminuye pero mucho más lento (a un ritmo de 1/3).
  // Matemáticamente, si zoom es 0.3, el texto debería escalar con respecto al canvas
  // un factor de Math.pow(zoom, -1/3) == 1 / Math.pow(zoom, 1/3). 
  // Esto hace que visualmente el texto encoja en pantalla, pero preserve la legibilidad 3 veces más tiempo.
  const textScale = zoom < 1 ? Math.pow(zoom, -1 / 3) : 1 / zoom;

  const adaptiveBusRadius = isLargeNetwork ? 12 : 20;
  const adaptiveFontSize = isLargeNetwork ? 10 : 12;

  // Generate bus positions for all buses including unpositioned ones
  const allBusPositions: Record<number, Point> = { ...busPositions };
  buses.forEach((bus) => {
    if (!allBusPositions[bus.id]) {
      const centerX = dimensions.width / 2;
      const centerY = dimensions.height / 2;
      const radius = Math.min(dimensions.width, dimensions.height) * 0.42;
      const idx = buses.indexOf(bus);
      const angle = (2 * Math.PI * idx) / busCount - Math.PI / 2;
      allBusPositions[bus.id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      };
    }
  });

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden' }}>
      <svg
        ref={canvasRef}
        className="network-canvas"
        width={dimensions.width}
        height={dimensions.height}
        viewBox={`${dimensions.width * (1 - 1 / zoom) / 2 + panOffset.x} ${dimensions.height * (1 - 1 / zoom) / 2 + panOffset.y} ${dimensions.width / zoom} ${dimensions.height / zoom}`}
        onClick={handleCanvasClick}
        onMouseDown={(e) => {
          // Start panning on empty canvas click in select mode
          if (mode === 'select' && e.button === 0 && !(e.target as Element).closest('g[data-bus]')) {
            setIsPanning(true);
            panStartRef.current = { x: e.clientX, y: e.clientY };
            panOffsetStartRef.current = { ...panOffset };
          }
        }}
        onMouseUp={() => { setDragging(null); setIsPanning(false); }}
        onMouseLeave={() => { setIsPanning(false); }}
        style={{ cursor: isPanning ? 'grabbing' : mode === 'select' && zoom > 1 ? 'grab' : mode === 'add-bus' || mode === 'add-line' ? 'crosshair' : 'default' }}
        onWheel={(e) => {
          e.preventDefault();
          const delta = e.deltaY > 0 ? -0.15 : 0.15;
          setZoom(z => Math.max(0.3, Math.min(3, z + delta)));
        }}
        onMouseMove={(e) => {
          // Pan: drag on empty canvas
          if (isPanning && !dragging) {
            const dx = (e.clientX - panStartRef.current.x) / zoom;
            const dy = (e.clientY - panStartRef.current.y) / zoom;
            setPanOffset({ x: panOffsetStartRef.current.x - dx, y: panOffsetStartRef.current.y - dy });
            return;
          }
          if (dragging) handleBusDrag(dragging, e);
          // Track mouse for line preview
          if (mode === 'add-line' && lineStart !== null) {
            const svgPt = screenToSvg(e);
            setMousePos(svgPt);
          }
        }}
      >
        <defs />{/* Arrowheads now drawn as inline polygons */}

        {/* Grid background removed */}

        {/* Lines */}
        {lines.map((line, idx) => {
          const fromPos = allBusPositions[line.from_bus];
          const toPos = allBusPositions[line.to_bus];
          if (!fromPos || !toPos) return null;

          const flow = getLineFlow(line.from_bus, line.to_bus);
          const loading = flow?.loading_percent || 0;
          const flowMw = flow?.flow_mw || 0;

          // Determine flow direction for arrow
          // If flow matches from->to direction, keep arrow from->to; otherwise reverse
          const flowResult = flow;
          let arrowFrom = fromPos;
          let arrowTo = toPos;
          if (flowResult) {
            if (flowResult.from_bus === line.from_bus) {
              // flow_mw > 0 => from->to; flow_mw < 0 => to->from
              if (flowResult.flow_mw < 0) {
                arrowFrom = toPos;
                arrowTo = fromPos;
              }
            } else {
              // flow is defined as to->from in results
              if (flowResult.flow_mw >= 0) {
                arrowFrom = toPos;
                arrowTo = fromPos;
              }
            }
          }

          // Calculate line geometry
          const midX = (fromPos.x + toPos.x) / 2;
          const midY = (fromPos.y + toPos.y) / 2;
          const dx = arrowTo.x - arrowFrom.x;
          const dy = arrowTo.y - arrowFrom.y;
          const lineLen = Math.sqrt(dx * dx + dy * dy);
          const angle = Math.atan2(toPos.y - fromPos.y, toPos.x - fromPos.x) * (180 / Math.PI);

          // Rotate label text so it's always readable
          let textAngle = angle;
          if (textAngle > 90) textAngle -= 180;
          if (textAngle < -90) textAngle += 180;

          return (
            <g key={`line-${idx}`}>
              {/* Line shadow */}
              <line
                x1={fromPos.x}
                y1={fromPos.y}
                x2={toPos.x}
                y2={toPos.y}
                stroke="rgba(0,0,0,0.1)"
                strokeWidth={getLineWidth(loading) + 2}
                style={{ pointerEvents: 'none' }}
              />
              {/* Main line */}
              <line
                x1={fromPos.x}
                y1={fromPos.y}
                x2={toPos.x}
                y2={toPos.y}
                stroke={line.status === 0 ? "#64748b" : getLineColor(loading)}
                strokeWidth={line.status === 0 ? 2 : getLineWidth(loading)}
                strokeDasharray={line.status === 0 ? "6,4" : "none"}
                style={{ cursor: 'context-menu' }}
                onClick={(e) => {
                  e.stopPropagation();
                  usePowerSystemStore.getState().setSelectedLine(idx);
                }}
                onContextMenu={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  usePowerSystemStore.getState().updateLine(idx, { status: line.status === 0 ? 1 : 0 });
                }}
              />
              {/* Visual disconnectors (breakers) for non-large networks */}
              {!isLargeNetwork && (() => {
                if (lineLen < 30) return null;
                // Use the pure geometric angle, NOT the arrowhead angle (which flips depending on flow direction)
                const realDx = toPos.x - fromPos.x;
                const realDy = toPos.y - fromPos.y;
                const realLen = Math.sqrt(realDx * realDx + realDy * realDy);
                const ux = realDx / realLen;
                const uy = realDy / realLen;

                // Offset carefully between the bus circle (15px) and the arrowhead tip
                const offset = adaptiveBusRadius + 5;
                const b1x = fromPos.x + ux * offset;
                const b1y = fromPos.y + uy * offset;
                const b2x = toPos.x - ux * offset;
                const b2y = toPos.y - uy * offset;

                // Real rotation angle for the rects based purely on from->to coordinates
                const realAngle = Math.atan2(realDy, realDx) * (180 / Math.PI);

                const bSize = 8;
                const isActive = line.status !== 0;
                // PowerWorld convention: Red solid for energized (closed), background+Green stroke for open
                const breakerFill = isActive ? "#ef4444" : "#0f1117";
                const breakerStroke = isActive ? "#ef4444" : "#10b981";

                return (
                  <g>
                    {/* Background wipe so the line doesn't strike directly through the open square */}
                    {!isActive && (
                      <>
                        <rect x={b1x - bSize / 2} y={b1y - bSize / 2} width={bSize} height={bSize} fill="#0f1117" transform={`rotate(${realAngle} ${b1x} ${b1y})`} />
                        <rect x={b2x - bSize / 2} y={b2y - bSize / 2} width={bSize} height={bSize} fill="#0f1117" transform={`rotate(${realAngle} ${b2x} ${b2y})`} />
                      </>
                    )}
                    <rect
                      x={b1x - bSize / 2}
                      y={b1y - bSize / 2}
                      width={bSize}
                      height={bSize}
                      rx="1"
                      fill={breakerFill}
                      stroke={breakerStroke}
                      strokeWidth="1.5"
                      style={{ cursor: 'pointer', transformOrigin: `${b1x}px ${b1y}px` }}
                      transform={`rotate(${realAngle})`}
                      onClick={(e) => {
                        e.stopPropagation();
                        usePowerSystemStore.getState().updateLine(idx, { status: isActive ? 0 : 1 });
                      }}
                    />
                    <rect
                      x={b2x - bSize / 2}
                      y={b2y - bSize / 2}
                      width={bSize}
                      height={bSize}
                      rx="1"
                      fill={breakerFill}
                      stroke={breakerStroke}
                      strokeWidth="1.5"
                      style={{ cursor: 'pointer', transformOrigin: `${b2x}px ${b2y}px` }}
                      transform={`rotate(${realAngle})`}
                      onClick={(e) => {
                        e.stopPropagation();
                        usePowerSystemStore.getState().updateLine(idx, { status: isActive ? 0 : 1 });
                      }}
                    />
                  </g>
                );
              })()}
              {/* Animated flow overlay (PowerWorld-style moving dots) */}
              {results && line.status !== 0 && Math.abs(flowMw) > 0.1 && (
                <line
                  x1={arrowFrom.x}
                  y1={arrowFrom.y}
                  x2={arrowTo.x}
                  y2={arrowTo.y}
                  stroke="white"
                  strokeWidth={getLineWidth(loading) - 0.5}
                  strokeDasharray="4 12"
                  strokeLinecap="round"
                  opacity={0.7}
                  style={{
                    pointerEvents: 'none',
                    animation: `flowDash ${Math.max(0.3, 2.5 - Math.abs(flowMw) / 80)}s linear infinite`,
                  }}
                />
              )}
              {/* Flow direction arrowhead */}
              {results && line.status !== 0 && Math.abs(flowMw) > 0.1 && lineLen > 50 && (() => {
                // Arrow scales with line width (loading)
                const lineW = getLineWidth(loading);
                const arrowSize = 6 + lineW * 2.5;  // 11 → 13.5 → 16
                // Unit direction vector from arrowFrom to arrowTo
                const ux = (arrowTo.x - arrowFrom.x) / lineLen;
                const uy = (arrowTo.y - arrowFrom.y) / lineLen;
                // Normal vector
                const nx = -uy;
                const ny = ux;
                // Tip of arrow (near target bus, just outside circle)
                const tipX = arrowTo.x - ux * 26;
                const tipY = arrowTo.y - uy * 26;
                // Base points
                const baseX = tipX - ux * arrowSize;
                const baseY = tipY - uy * arrowSize;
                const halfW = arrowSize * 0.55;
                const p1x = baseX + nx * halfW;
                const p1y = baseY + ny * halfW;
                const p2x = baseX - nx * halfW;
                const p2y = baseY - ny * halfW;
                const arrowColor = getLineColor(loading);
                return (
                  <polygon
                    points={`${tipX},${tipY} ${p1x},${p1y} ${p2x},${p2y}`}
                    fill={arrowColor}
                    style={{ pointerEvents: 'none' }}
                  />
                );
              })()}
              {/* Flow label (rotated to follow line) */}
              {results && line.status !== 0 && (
                <g transform={`translate(${midX}, ${midY})`}>
                  <g transform={`scale(${textScale})`}>
                    <g transform={`rotate(${textAngle})`}>
                      <rect
                        x={-28}
                        y={-12}
                        width={56}
                        height={18}
                        fill="rgba(15, 23, 42, 0.9)"
                        rx={4}
                        stroke="#475569"
                        strokeWidth={1}
                      />
                      <text
                        x={0}
                        y={1}
                        dy="0.30em"
                        textAnchor="middle"
                        fontSize="11"
                        fill="#fff"
                        fontWeight="600"
                        style={{ pointerEvents: 'none' }}
                      >
                        {Math.abs(flowMw).toFixed(0)} MW
                      </text>
                    </g>
                  </g>
                </g>
              )}
            </g>
          );
        })}

        {/* Temporary line when adding line */}
        {mode === 'add-line' && lineStart && (
          <line
            x1={allBusPositions[lineStart]?.x || 0}
            y1={allBusPositions[lineStart]?.y || 0}
            x2={dimensions.width / 2}
            y2={dimensions.height / 2}
            stroke="#6366f1"
            strokeWidth={2}
            strokeDasharray="5,5"
            style={{ pointerEvents: 'none' }}
          />
        )}

        {/* Buses */}
        {buses.map((bus) => {
          const pos = allBusPositions[bus.id] || { x: 0, y: 0 };
          const hasLoad = loads.some((l) => l.bus === bus.id);
          const loadMW = getLoadMW(bus.id);
          const curtail = getCurtailment(bus.id);

          return (
            <g
              key={`bus-${bus.id}`}
              data-bus={bus.id}
              transform={`translate(${pos.x}, ${pos.y})`}
              style={{ cursor: 'pointer' }}
              onClick={(e) => handleBusClick(bus.id, e)}
              onMouseDown={(e) => {
                e.stopPropagation();
                setDragging(bus.id);
              }}
            >
              {/* Bus circle */}
              {mode === 'add-line' && (
                <circle
                  r={adaptiveBusRadius + 4}
                  fill="none"
                  stroke={lineStart === bus.id ? '#3b82f6' : '#93c5fd'}
                  strokeWidth={lineStart === bus.id ? 3 : 2}
                  strokeDasharray={lineStart === bus.id ? 'none' : '4,3'}
                  opacity={0.8}
                />
              )}
              <circle
                r={adaptiveBusRadius}
                fill={getBusColor(bus.type)}
                stroke={selectedBus === bus.id ? '#818cf8' : '#2e3348'}
                strokeWidth={selectedBus === bus.id ? 3 : 2}
                style={{ filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))' }}
                onContextMenu={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  addGenerator({
                    bus: bus.id,
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
                }}
              />
              {/* Bus label with pill */}
              {(() => {
                const label = bus.name || String(bus.id);
                const pillW = Math.max(isLargeNetwork ? 20 : 28, label.length * (isLargeNetwork ? 6 : 8) + 8);
                const pillH = isLargeNetwork ? 14 : 18;
                return (
                  <g transform={`scale(${textScale})`}>
                    {/* Reverse margin to keep it docked at the edge of the circle despite scaling */}
                    <g transform={`translate(0, ${-(adaptiveBusRadius / textScale) - pillH - 4})`}>
                      <rect x={-pillW / 2} y={0} width={pillW} height={pillH} rx="4" fill="rgba(36, 40, 56, 0.9)" stroke="#4b5563" strokeWidth="1" />
                      <text
                        textAnchor="middle"
                        y={pillH / 2}
                        dy="0.35em"
                        fill="#fff"
                        fontSize={adaptiveFontSize}
                        fontWeight="bold"
                        style={{ pointerEvents: 'none' }}
                      >
                        {label}
                      </text>
                    </g>
                  </g>
                );
              })()}

              {/* Generator indicator — support multiple per bus */}
              {(() => {
                const busGenerators = generators.filter(g => g.bus === bus.id);
                return busGenerators.map((gen, gIdx) => {
                  const isActive = gen.status !== 0;
                  // Try to find result by ID, then by bus index as fallback
                  let genResult = results?.generator_results.find(r => r.id === gen.id);
                  if (!genResult && results) {
                    // Fallback: finding the i-th generator of this bus in results
                    const sameBusResults = results.generator_results.filter(r => r.bus === bus.id);
                    genResult = sameBusResults[gIdx];
                  }
                  const p_mw = genResult?.pg ?? null;

                  // Offset if multiple generators. Start from middle and go down.
                  const spacing = isLargeNetwork ? 14 : 22;
                  const yOffset = gIdx * spacing;
                  const xOffset = adaptiveBusRadius + 4;

                  return (
                    <g
                      key={`gen-${gen.id}`}
                      transform={`translate(${xOffset}, ${yOffset}) scale(${textScale})`}
                      onClick={(e) => {
                        e.stopPropagation();
                        usePowerSystemStore.getState().setSelectedGenerator(gen.id || null);
                      }}
                    >
                      <title>{gen.name || gen.id}</title>
                      <circle
                        r={isLargeNetwork ? 5 : 8}
                        fill={isActive ? "#8b5cf6" : "#64748b"}
                        stroke={selectedGenerator === gen.id ? "#fff" : "#2e3348"}
                        strokeWidth={isLargeNetwork ? 1 : selectedGenerator === gen.id ? 2.5 : 2}
                        style={{ cursor: 'context-menu', filter: selectedGenerator === gen.id ? 'drop-shadow(0 0 4px #8b5cf6)' : 'none' }}
                        onContextMenu={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          usePowerSystemStore.getState().updateGenerator(gen.id!, { status: isActive ? 0 : 1 });
                        }}
                      />
                      <text textAnchor="middle" dy="0.35em" fill="white" fontSize={isLargeNetwork ? 8 : 11} fontWeight="bold" style={{ pointerEvents: 'none' }}>
                        G
                      </text>
                      {/* Gen MW label */}
                      {results && p_mw !== null && isActive && (
                        <g transform="translate(14, 0)">
                          <rect x={-2} y={-9} width={46} height={18} rx="4" fill="#8b5cf6" opacity={1} stroke="#2e3348" strokeWidth="1" />
                          <text x={21} dy="0.35em" textAnchor="middle" fill="#fff" fontSize="11" fontWeight="bold" style={{ pointerEvents: 'none' }}>
                            {p_mw.toFixed(0)} MW
                          </text>
                        </g>
                      )}
                      {!isActive && (
                        <g transform="translate(14, 0)">
                          <rect x={-2} y={-9} width={34} height={18} rx="4" fill="#64748b" opacity={0.8} stroke="#2e3348" strokeWidth="1" />
                          <text x={15} dy="0.35em" textAnchor="middle" fill="#fff" fontSize="10" fontWeight="bold" style={{ pointerEvents: 'none' }}>
                            OFF
                          </text>
                        </g>
                      )}
                    </g>
                  );
                });
              })()}

              {/* Load indicator — simplified for large networks */}
              {hasLoad && (
                <g transform={`translate(${-adaptiveBusRadius - 4}, 0) scale(${textScale})`}>
                  <circle r={isLargeNetwork ? 5 : 8} fill="#f97316" stroke="#2e3348" strokeWidth={isLargeNetwork ? 1 : 2} />
                  <text textAnchor="middle" dy="0.35em" fill="white" fontSize={isLargeNetwork ? 8 : 11} fontWeight="bold" style={{ pointerEvents: 'none' }}>
                    L
                  </text>
                  {/* Load MW label — Always show, scale inversely */}
                  {loadMW !== null && (
                    <g transform="translate(-14, 0)">
                      <rect x={-44} y={-9} width={46} height={18} rx="4" fill="#f97316" opacity={1} stroke="#2e3348" strokeWidth="1" />
                      <text x={-21} dy="0.35em" textAnchor="middle" fill="#fff" fontSize="11" fontWeight="bold" style={{ pointerEvents: 'none' }}>
                        {loadMW.toFixed(0)} MW
                      </text>
                    </g>
                  )}
                  {/* Curtailment label */}
                  {results && curtail > 0.01 && (
                    <g transform="translate(-14, 16)">
                      <rect x={-48} y={-9} width={56} height={18} rx="4" fill="#ef4444" opacity={1} stroke="#2e3348" strokeWidth="1" />
                      <text x={-20} dy="0.35em" textAnchor="middle" fill="#fff" fontSize="10" fontWeight="bold" style={{ pointerEvents: 'none' }}>
                        ✂ {curtail.toFixed(0)} MW
                      </text>
                    </g>
                  )}
                </g>
              )}

              {/* Voltage angle and LMP — Always show, scale inversely */}
              {results && (() => {
                const busGenerators = generators.filter(g => g.bus === bus.id);
                // Dynamically push results down if there are many generators to avoid overlap
                const genOffset = Math.max(0, busGenerators.length - 1) * (isLargeNetwork ? 14 : 22);
                const yOffset = adaptiveBusRadius + 26 + genOffset;
                return (
                  <g transform={`translate(0, ${yOffset}) scale(${textScale})`}>
                    <rect x="-30" y="-12" width="60" height="28" rx="4" fill="rgba(15, 23, 42, 0.75)" stroke="#2e3348" strokeWidth="1" />
                    <text y="-2" textAnchor="middle" fontSize="11" fill="#e2e8f0" fontWeight="500" style={{ pointerEvents: 'none' }}>
                      {results.bus_results.find((b) => b.bus === bus.id)?.va.toFixed(1)}°
                    </text>
                    <text y="10" textAnchor="middle" fontSize="11" fill="#a78bfa" fontWeight="700" style={{ pointerEvents: 'none' }}>
                      ${(results.bus_results.find((b) => b.bus === bus.id)?.marginal_cost || 0).toFixed(0)}/MWh
                    </text>
                  </g>
                );
              })()}
            </g>
          );
        })}

        {/* Empty state */}
        {buses.length === 0 && (
          <text
            x={dimensions.width / 2}
            y={dimensions.height / 2 - 20}
            textAnchor="middle"
            fill="#8891a8"
            fontSize="16"
            fontWeight="500"
          >
            Click &quot;Load Example&quot; to load IEEE 9-bus system
          </text>
        )}
        {buses.length === 0 && (
          <text
            x={dimensions.width / 2}
            y={dimensions.height / 2 + 10}
            textAnchor="middle"
            fill="#8891a8"
            fontSize="14"
            fontWeight="500"
          >
            or use the toolbar to add buses
          </text>
        )}
        {/* Line-drawing rubber band preview */}
        {mode === 'add-line' && lineStart !== null && allBusPositions[lineStart] && (
          <line
            x1={allBusPositions[lineStart].x}
            y1={allBusPositions[lineStart].y}
            x2={mousePos.x}
            y2={mousePos.y}
            stroke="#6366f1"
            strokeWidth={2}
            strokeDasharray="6,4"
            opacity={0.6}
            style={{ pointerEvents: 'none' }}
          />
        )}
      </svg>

      {/* Floating canvas toolbar */}
      <div style={{
        position: 'absolute',
        top: '0.75rem',
        right: '0.75rem',
        display: 'flex',
        gap: '0.4rem',
        zIndex: 20,
      }}>
        <button
          className={`tool-btn ${mode === 'add-bus' ? 'active' : ''}`}
          onClick={() => { setMode(mode === 'add-bus' ? 'select' : 'add-bus'); setLineStart(null); }}
          title="Add Bus — click on canvas to place"
          style={{ fontSize: '0.8rem', padding: '0.35rem 0.6rem' }}
        >
          ⊕ Bus
        </button>
        <button
          className={`tool-btn ${mode === 'add-line' ? 'active' : ''}`}
          onClick={() => { setMode(mode === 'add-line' ? 'select' : 'add-line'); setLineStart(null); }}
          title="Add Line — click two buses to connect"
          style={{ fontSize: '0.8rem', padding: '0.35rem 0.6rem' }}
        >
          ⟋ Line
        </button>
        {mode !== 'select' && (
          <button
            className="tool-btn"
            onClick={() => { setMode('select'); setLineStart(null); }}
            title="Cancel"
            style={{ fontSize: '0.8rem', padding: '0.35rem 0.6rem', color: '#ef4444' }}
          >
            ✕
          </button>
        )}
        {/* Zoom controls */}
        <div style={{ width: '1px', height: '20px', background: '#2e3348', alignSelf: 'center' }} />
        <button
          className="tool-btn"
          onClick={() => setZoom(z => Math.min(3, z + 0.2))}
          title="Zoom In"
          style={{ fontSize: '1rem', padding: '0.35rem 0.5rem', lineHeight: 1 }}
        >
          +
        </button>
        <span style={{ fontSize: '0.7rem', color: '#8891a8', alignSelf: 'center', minWidth: '32px', textAlign: 'center' }}>
          {Math.round(zoom * 100)}%
        </span>
        <button
          className="tool-btn"
          onClick={() => setZoom(z => Math.max(0.3, z - 0.2))}
          title="Zoom Out"
          style={{ fontSize: '1rem', padding: '0.35rem 0.5rem', lineHeight: 1 }}
        >
          −
        </button>
        <button
          className="tool-btn"
          onClick={() => { setZoom(1); setPanOffset({ x: 0, y: 0 }); }}
          title="Reset Zoom"
          style={{ fontSize: '0.7rem', padding: '0.35rem 0.5rem' }}
        >
          ⊡
        </button>
      </div>

      {/* Mode status indicator */}
      {
        mode !== 'select' && (
          <div style={{
            position: 'absolute',
            bottom: '0.75rem',
            left: '50%',
            transform: 'translateX(-50%)',
            background: '#242838',
            color: '#e8eaf0',
            padding: '0.4rem 1rem',
            borderRadius: '20px',
            fontSize: '0.8rem',
            fontWeight: 600,
            zIndex: 20,
            boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
          }}>
            {mode === 'add-bus' ? '🖱️ Click on canvas to place new bus' :
              lineStart === null ? '🖱️ Click first bus to start line' :
                `🖱️ Click second bus to connect from Bus ${lineStart}`}
          </div>
        )}
    </div>
  );
}
