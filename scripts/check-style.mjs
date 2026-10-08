// Guardrail for DESIGN_GUIDELINES.md: flags raw colors, stray fonts and bold weights outside the token files.
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));
const ALLOWED = new Set(["css/tokens.css"]);
const SKIP_DIRS = new Set(["node_modules", ".git", "assets", "scripts"]);
const EXT = /\.(css|html|js|mjs)$/;

const rules = [
  { name: "raw hex color", re: /#[0-9a-fA-F]{3,8}\b(?![\w-])/g, skip: (l) => /href=|id=|url\(#|&#|\bhash\b/.test(l) },
  { name: "raw rgb()/hsl() color", re: /\b(?:rgb|rgba|hsl|hsla)\(/g },
  { name: "font-family outside tokens", re: /font-family\s*:(?!\s*var\()/g },
  { name: "bold font-weight", re: /font-weight\s*:\s*(?:bold|[6-9]00)/g },
  { name: "pure white/black keyword", re: /:\s*(?:white|black)\s*[;}]/g },
];

function* walk(dir) {
  for (const name of readdirSync(dir)) {
    if (SKIP_DIRS.has(name)) continue;
    const p = join(dir, name);
    if (statSync(p).isDirectory()) yield* walk(p);
    else if (EXT.test(name)) yield p;
  }
}

let problems = 0;
for (const file of walk(root)) {
  const rel = relative(root, file).split(sep).join("/");
  if (ALLOWED.has(rel)) continue;
  readFileSync(file, "utf8").split("\n").forEach((line, i) => {
    for (const r of rules) {
      if (r.skip?.(line)) continue;
      if (r.re.test(line)) {
        console.log(`${rel}:${i + 1}  ${r.name}\n    ${line.trim()}`);
        problems++;
      }
      r.re.lastIndex = 0;
    }
  });
}

if (problems) {
  console.log(`\n${problems} style problem(s). Use tokens from css/tokens.css (see DESIGN_GUIDELINES.md).`);
  process.exit(1);
}
console.log("Style check passed.");
