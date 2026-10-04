// Cross-runtime parity check: the TypeScript model runtime must produce the same probabilities as the Python one.
// Usage (from frontend/): node scripts/parity.mjs  -> prints JSON predictions for the probe sentences.
// backend/ml/parity.py prints the same structure from Python; the two are compared by backend/tests/test_parity.py.
import { readFileSync, writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { execSync } from "node:child_process";

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, "..", "..");
const probes = JSON.parse(readFileSync(join(root, "backend", "ml", "parity_probes.json"), "utf8"));

// Compile tinyModel.ts to a temp ES module with the project's TypeScript, then import it.
const out = mkdtempSync(join(tmpdir(), "karibu-parity-"));
execSync(
  `npx tsc ${join(here, "..", "src", "lib", "tinyModel.ts")} --outDir ${out} --module es2020 --target es2020 --moduleResolution bundler --skipLibCheck`,
  { stdio: "inherit", cwd: join(here, "..") }
);
writeFileSync(join(out, "package.json"), JSON.stringify({ type: "module" }));
const { TinyModel, splitClauses } = await import(pathToFileURL(join(out, "tinyModel.js")).href);

const result = { models: {}, clauses: {} };
for (const name of ["intent", "langid", "aspect", "sentiment"]) {
  const artifact = JSON.parse(readFileSync(join(root, "shared", "models", `${name}.json`), "utf8"));
  const m = new TinyModel(artifact);
  result.models[name] = probes.sentences.map((s) => {
    const p = m.predict(s);
    return { text: s, label: p.label, confidence: Number(p.confidence.toFixed(6)) };
  });
}
for (const r of probes.reviews) result.clauses[r] = splitClauses(r);
console.log(JSON.stringify(result));
