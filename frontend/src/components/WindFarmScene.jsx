import { useI18n } from "../i18n/LanguageProvider";
import { useEffect, useId, useState } from "react";

// One outline is shared by the landscape clip and its visible border.
const SCENE_OUTLINE = "M290 24 H644 C708 24 740 96 740 180 V370 C740 502 630 580 494 580 H126 C54 580 20 530 20 452 V278 C20 138 140 24 290 24 Z";

const Turbine = ({ x, y, scale = 1, speed = "8s", delay = "0s", reducedMotion }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`} className="turbine-unit">
    <ellipse className="turbine-shadow" cx="-18" cy="134" rx="36" ry="5" />
    <path className="turbine-tower" d="M-3 7 L3 7 L10 132 L-10 132 Z" />
    <g className="turbine-rotor">
      {!reducedMotion && <animateTransform
        attributeName="transform"
        type="rotate"
        from="0 0 0"
        to="360 0 0"
        dur={speed}
        begin={delay}
        repeatCount="indefinite"
      />}
      <path d="M0 -4 C14 -24 18 -58 7 -91 C2 -97 -3 -92 -3 -82 L-2 -7 Z" />
      <path d="M0 -4 C14 -24 18 -58 7 -91 C2 -97 -3 -92 -3 -82 L-2 -7 Z" transform="rotate(120)" />
      <path d="M0 -4 C14 -24 18 -58 7 -91 C2 -97 -3 -92 -3 -82 L-2 -7 Z" transform="rotate(240)" />
      <circle r="7" />
      <circle className="hub-light" r="2.5" />
    </g>
  </g>
);

export default function WindFarmScene() {
  const { t } = useI18n();
  const id = useId().replace(/:/g, "");
  const [reducedMotion, setReducedMotion] = useState(() => window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  useEffect(() => {
    const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReducedMotion(preference.matches);
    preference.addEventListener("change", update);
    return () => preference.removeEventListener("change", update);
  }, []);

  return (
    <div className="wind-scene" aria-label={t("Animated wind farm visualization")}>
      <svg className="wind-landscape" viewBox="0 0 760 600" role="img" aria-label={t("Three animated wind turbines in a curved landscape")}>
        <defs>
          <clipPath id={`${id}-clip`}><path d={SCENE_OUTLINE} /></clipPath>
          <radialGradient id={`${id}-sky`} cx="35%" cy="38%" r="80%">
            <stop offset="0" stopColor="var(--scene-sky-glow)" />
            <stop offset="1" stopColor="var(--scene-sky-base)" />
          </radialGradient>
          <radialGradient id={`${id}-haze`}>
            <stop offset="0" stopColor="var(--scene-haze)" stopOpacity=".5" />
            <stop offset="1" stopColor="var(--scene-haze)" stopOpacity="0" />
          </radialGradient>
          <linearGradient id={`${id}-ground`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="var(--scene-ground-top)" />
            <stop offset="1" stopColor="var(--scene-ground-bottom)" />
          </linearGradient>
        </defs>
        <g clipPath={`url(#${id}-clip)`}>
          <rect width="760" height="600" fill={`url(#${id}-sky)`} />
          <ellipse className="scene-haze" cx="545" cy="270" rx="300" ry="250" fill={`url(#${id}-haze)`} />
          <g className="scene-wind-lines" aria-hidden="true">
            <path d="M-120 185 H760" /><path d="M-70 248 H810" />
            <path d="M-160 305 H720" /><path d="M-30 356 H850" />
          </g>
          <path className="far-ridge" d="M-30 420 C115 340 215 405 350 355 S585 380 790 296 V640 H-30 Z" />
          <path d="M-30 474 C112 402 230 446 348 409 S579 462 790 376 V640 H-30 Z" fill={`url(#${id}-ground)`} />
          <Turbine x={180} y={330} scale={0.72} speed="10s" delay="-2s" reducedMotion={reducedMotion} />
          <Turbine x={420} y={286} scale={1.08} speed="7s" delay="-4s" reducedMotion={reducedMotion} />
          <Turbine x={635} y={325} scale={0.82} speed="8.5s" delay="-1s" reducedMotion={reducedMotion} />
          <path className="ground-trace" d="M65 489 C230 446 337 506 483 462 S635 465 727 431" />
        </g>
        <path className="scene-outline" d={SCENE_OUTLINE} />
      </svg>
      <div className="scene-telemetry" aria-label={t("Wind farm live status")}>
        <span className="scene-telemetry-title">{t("Wind farm telemetry")}</span>
        <span className="scene-telemetry-rule" aria-hidden="true" />
        <div className="scene-telemetry-item">
          <span>{t("Wind field")}</span>
          <strong><i />{t("Live")}</strong>
        </div>
        <div className="scene-telemetry-item">
          <span>{t("Farm state")}</span>
          <strong>{t("Nominal")}</strong>
        </div>
      </div>
    </div>
  );
}
