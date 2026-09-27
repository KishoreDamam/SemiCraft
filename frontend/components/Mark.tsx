/**
 * SemiCraft mark: a quad flat package seen from above, pin 1 marked. Drawn
 * with the current text colour so it follows the theme.
 */
export function Mark({ className }: { className?: string }) {
  const pins = [7, 10, 13];
  return (
    <svg
      viewBox="0 0 20 20"
      aria-hidden
      className={className}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.4}
      strokeLinecap="square"
    >
      <rect x={4.5} y={4.5} width={11} height={11} />
      {pins.map((p) => (
        <g key={p}>
          <path d={`M${p} 1.5V4.5`} />
          <path d={`M${p} 15.5V18.5`} />
          <path d={`M1.5 ${p}H4.5`} />
          <path d={`M15.5 ${p}H18.5`} />
        </g>
      ))}
      <circle cx={7.4} cy={7.4} r={0.9} fill="currentColor" stroke="none" />
    </svg>
  );
}
