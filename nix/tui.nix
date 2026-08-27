# nix/tui.nix — Sonic TUI (Ink/React) compiled with tsc and bundled
{ pkgs, sonicNpmLib, ... }:
let
  npm = sonicNpmLib.mkNpmPassthru { folder = "ui-tui"; attr = "tui"; pname = "sonic-tui"; };

  packageJson = builtins.fromJSON (builtins.readFile (npm.src + "/ui-tui/package.json"));
  version = packageJson.version;
in
pkgs.buildNpmPackage (npm // {
  pname = "sonic-tui";
  inherit version;

  doCheck = false;

  buildPhase = ''
    # esbuild bundles everything — no need for tsc or vite.
    # Run from the workspace root where node_modules/ lives.
    node ui-tui/scripts/build.mjs
  '';

  installPhase = ''
    runHook preInstall

    mkdir -p $out/lib/sonic-tui
    # esbuild writes to ui-tui/dist/ from the source root (no cd).
    cp -r ui-tui/dist $out/lib/sonic-tui/dist

    # package.json kept for "type": "module" resolution on `node dist/entry.js`.
    cp ui-tui/package.json $out/lib/sonic-tui/

    runHook postInstall
  '';
})
