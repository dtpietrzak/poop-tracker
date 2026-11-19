import { defineConfig } from "cf/config";

// Assets-only Worker: the static PWA in ./public, deployed with `cf deploy ./public`.
export default defineConfig({
  worker: {
    name: "poop-tracker",
    compatibilityDate: "2026-11-01",
    domains: ["poop.davidp.dev"],
  },
});
