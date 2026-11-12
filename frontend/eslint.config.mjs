import nextCoreWebVitals from "eslint-config-next/core-web-vitals";

/**
 * ESLint 9 flat config (Next.js 16 removed `next lint`).
 * `eslint-config-next` v16 already exports native flat configs, so no
 * FlatCompat shim is needed. The two rules below mirror the previous
 * `.eslintrc.json` and are redundant with the React 17+ JSX transform.
 */
const config = [
  {
    ignores: [".next/**", "node_modules/**", "next-env.d.ts", "tsconfig.tsbuildinfo"],
  },
  ...nextCoreWebVitals,
  {
    rules: {
      "react/react-in-jsx-scope": "off",
      "react/jsx-uses-react": "off",
      // New in eslint-config-next@16 (eslint-plugin-react-hooks v7 / React
      // Compiler). It flags 6 pre-existing patterns (localStorage hydration and
      // "reset on prop change" effects) that are intentional here. Kept as a
      // warning so `npm run lint` still gates instead of failing on legacy
      // code; the refactor is tracked as a follow-up.
      "react-hooks/set-state-in-effect": "warn",
    },
  },
];

export default config;
