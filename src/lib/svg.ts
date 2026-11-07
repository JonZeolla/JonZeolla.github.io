/** Intrinsic size of an SVG from its root viewBox, or undefined when it has none. */
export function viewBoxSize(svg: string): { width: number; height: number } | undefined {
  const root = svg.match(/<svg\b[^>]*>/)?.[0];
  const vb = root?.match(/\bviewBox\s*=\s*["']([^"']+)["']/i)?.[1].trim().split(/[\s,]+/).map(Number);
  if (!vb || vb.length !== 4 || !(vb[2] > 0 && vb[3] > 0)) return undefined;
  return { width: vb[2], height: vb[3] };
}
