/**
 * Decorative left-panel artwork for the login screen: a day-shaped demand
 * curve (grey) plus an amber "net load after solar" curve with a midday
 * dip. Pure inline SVG, animated with a slow stroke-draw so it reads as
 * alive without being noisy — no gradients-on-gradients, no glassmorphism.
 */
export function LoadCurveArt() {
  // Two 24-hour curves sampled at 25 points (0..24h), viewBox 0..960 x 0..320.
  const grossLoad = [
    190, 175, 165, 160, 162, 175, 205, 240, 262, 270, 268, 260, 255, 258, 262, 268, 278, 292, 300,
    295, 278, 250, 225, 205, 190,
  ];
  const netLoad = [
    190, 175, 165, 160, 162, 175, 205, 232, 220, 190, 150, 118, 100, 95, 102, 130, 175, 240, 300,
    295, 278, 250, 225, 205, 190,
  ];

  const toPath = (values: number[]) => {
    const w = 960;
    const h = 320;
    const max = 320;
    const step = w / (values.length - 1);
    return values
      .map(
        (v, i) =>
          `${i === 0 ? "M" : "L"} ${(i * step).toFixed(1)} ${(h - (v / max) * h).toFixed(1)}`,
      )
      .join(" ");
  };

  return (
    <svg
      viewBox="0 0 960 320"
      className="h-full w-full"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        <clipPath id="curve-clip">
          <rect x="0" y="0" width="960" height="320" />
        </clipPath>
      </defs>

      {/* Baseline grid */}
      {[0, 1, 2, 3].map((i) => (
        <line
          key={i}
          x1="0"
          x2="960"
          y1={80 * i}
          y2={80 * i}
          stroke="#ffffff"
          strokeOpacity="0.06"
          strokeWidth="1"
        />
      ))}

      <g clipPath="url(#curve-clip)">
        {/* Gross load (grey) */}
        <path
          d={toPath(grossLoad)}
          stroke="#8b929b"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="lpmf-draw"
          pathLength={1}
        />
        {/* Net load after solar (amber), with midday dip */}
        <path
          d={toPath(netLoad)}
          stroke="#e39b16"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="lpmf-draw lpmf-draw-delay"
          pathLength={1}
        />
      </g>
    </svg>
  );
}
