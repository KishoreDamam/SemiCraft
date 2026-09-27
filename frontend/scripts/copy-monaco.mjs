// Copy Monaco's AMD build into public/ so the editor is served by this app
// rather than a CDN. Restricted and air-gapped networks — common in
// semiconductor shops — block cdn.jsdelivr.net, and the preview would then
// never leave "Loading…". Runs before dev and build; public/monaco is
// gitignored.
import { cpSync, existsSync, readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const pkgDir = dirname(require.resolve("monaco-editor/package.json"));
const { version } = JSON.parse(readFileSync(join(pkgDir, "package.json"), "utf8"));

const here = dirname(fileURLToPath(import.meta.url));
const dest = join(here, "..", "public", "monaco");
const stamp = join(dest, ".version");

if (existsSync(stamp) && readFileSync(stamp, "utf8") === version) process.exit(0);

cpSync(join(pkgDir, "min", "vs"), join(dest, "vs"), { recursive: true });
writeFileSync(stamp, version);
console.log(`copied monaco-editor ${version} to public/monaco`);
