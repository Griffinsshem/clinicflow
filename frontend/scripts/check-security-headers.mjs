#!/usr/bin/env node
/**
 * Check that a running ClinicFlow frontend sends its security headers.
 *
 *   node scripts/check-security-headers.mjs https://clinicflow-mu-nine.vercel.app
 *   node scripts/check-security-headers.mjs http://localhost:3000
 *
 * Checks the landing page, the login page, an unknown URL (404) and an
 * API route. Exits with code 1 if anything is missing, so it can run in
 * CI after a deploy. Needs Node 18+ (built-in fetch); no dependencies.
 */

const base = (process.argv[2] ?? "http://localhost:3000").replace(/\/$/, "");
const isHttps = base.startsWith("https://");

const PAGE_HEADERS = {
  "x-content-type-options": (v) => v === "nosniff",
  "x-frame-options": (v) => v === "DENY",
  "referrer-policy": (v) => v === "strict-origin-when-cross-origin",
  "permissions-policy": (v) => v.includes("camera=()") && v.includes("geolocation=()"),
  "cross-origin-opener-policy": (v) => v === "same-origin",
  "strict-transport-security": (v) => v.includes("max-age="),
};

const CSP_RULES = [
  ["has a nonce for scripts", (csp) => /script-src[^;]*'nonce-[A-Za-z0-9+/=]+'/.test(csp)],
  ["does not allow inline scripts", (csp) => !/script-src[^;]*'unsafe-inline'/.test(csp)],
  ["does not allow eval in production", (csp) => !/'unsafe-eval'/.test(csp)],
  ["blocks framing", (csp) => csp.includes("frame-ancestors 'none'")],
  ["blocks plugins", (csp) => csp.includes("object-src 'none'")],
  ["limits connections to this site", (csp) => csp.includes("connect-src 'self'")],
  ...(isHttps
    ? [["upgrades insecure requests", (csp) => csp.includes("upgrade-insecure-requests")]]
    : []),
];

let failures = 0;
const ok = (msg) => console.log(`  ✓ ${msg}`);
const fail = (msg) => {
  failures += 1;
  console.log(`  ✗ ${msg}`);
};

async function get(path, init = {}) {
  return fetch(base + path, { redirect: "manual", ...init });
}

async function checkPage(path, expectedStatus) {
  console.log(`\n${path}`);
  const response = await get(path);
  if (response.status === expectedStatus) ok(`status ${response.status}`);
  else fail(`status ${response.status}, expected ${expectedStatus}`);

  for (const [name, isValid] of Object.entries(PAGE_HEADERS)) {
    const value = response.headers.get(name);
    if (value && isValid(value)) ok(name);
    else fail(`${name}: ${value ?? "missing"}`);
  }

  const csp = response.headers.get("content-security-policy");
  if (!csp) {
    fail("content-security-policy: missing");
    return null;
  }
  for (const [label, rule] of CSP_RULES) {
    if (rule(csp)) ok(`CSP ${label}`);
    else fail(`CSP ${label}`);
  }
  return csp.match(/'nonce-([^']+)'/)?.[1] ?? null;
}

console.log(`Checking security headers on ${base}`);

const first = await checkPage("/", 200);
const second = await checkPage("/", 200);
console.log("\nNonce");
if (first && second && first !== second) ok("is different on every request");
else fail("is not changing between requests");

await checkPage("/login", 200);
await checkPage("/this-page-does-not-exist", 404);

console.log("\n/api/proxy/patients (signed out)");
const api = await get("/api/proxy/patients");
const cacheControl = api.headers.get("cache-control") ?? "";
if (cacheControl.includes("no-store")) ok("cache-control: no-store");
else fail(`cache-control: ${cacheControl || "missing"}`);
if (api.headers.get("x-content-type-options") === "nosniff") ok("x-content-type-options");
else fail("x-content-type-options missing");

console.log(
  failures === 0
    ? "\nAll security headers present."
    : `\n${failures} problem(s) found.`,
);
process.exit(failures === 0 ? 0 : 1);
