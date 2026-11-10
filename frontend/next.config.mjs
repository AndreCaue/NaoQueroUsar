import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  // D-3: pin the workspace root to this package. Without it, Next walks up and
  // finds an unrelated lockfile (C:\Users\AndreC\package-lock.json), emits the
  // "inferred your workspace root" warning and traces the wrong tree.
  outputFileTracingRoot: __dirname,
};

export default nextConfig;
