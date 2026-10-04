// Copies <repo>/shared (models + templates) into public/shared so Vite serves it at /shared in dev and
// bundles it into dist for the single-container build. One source of truth: never edit public/shared by hand.
import { cpSync, existsSync, mkdirSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const src = resolve(here, "..", "..", "shared");
const dst = resolve(here, "..", "public", "shared");

if (!existsSync(src)) {
  console.error(`[copy-shared] ${src} not found. Run "python -m ml.train" in backend/ first.`);
  process.exit(1);
}
rmSync(dst, { recursive: true, force: true });
mkdirSync(dst, { recursive: true });
cpSync(src, dst, { recursive: true, filter: (p) => !p.endsWith("METRICS.md") || true });
console.log(`[copy-shared] ${src} -> ${dst}`);
