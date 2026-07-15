# nix/tui.nix — Sonic TUI (Ink/React) compiled with tsc and bundled
{ pkgs, sonicNpmLib, ... }:
let
  src = ../ui-tui;
  npmDeps = pkgs.fetchNpmDeps {
    inherit src;
    hash = "sha256-aC+wKz1VRmHsIDd5vB19w+5vuXeAvMqBFRuJ9yNDz7M=";
  };

  npm = sonicNpmLib.mkNpmPassthru { folder = "ui-tui"; attr = "tui"; pname = "sonic-tui"; };

  packageJson = builtins.fromJSON (builtins.readFile (src + "/package.json"));
  version = packageJson.version;
in
pkgs.buildNpmPackage (npm // {
  pname = "sonic-tui";
  inherit src npmDeps version;

  doCheck = false;
  npmFlags = [ "--legacy-peer-deps" ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/lib/sonic-tui

    # Single self-contained bundle built by scripts/build.mjs (esbuild).
    cp -r dist $out/lib/sonic-tui/dist

    # package.json kept for "type": "module" resolution on `node dist/entry.js`.
    cp package.json $out/lib/sonic-tui/

    runHook postInstall
  '';
})
