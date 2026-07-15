# nix/tui.nix — Lightning TUI (Ink/React) compiled with tsc and bundled
{ pkgs, lightningNpmLib, ... }:
let
  src = ../ui-tui;
  npmDeps = pkgs.fetchNpmDeps {
    inherit src;
    hash = "sha256-aC+wKz1VRmHsIDd5vB19w+5vuXeAvMqBFRuJ9yNDz7M=";
  };

  npm = lightningNpmLib.mkNpmPassthru { folder = "ui-tui"; attr = "tui"; pname = "lightning-tui"; };

  packageJson = builtins.fromJSON (builtins.readFile (src + "/package.json"));
  version = packageJson.version;
in
pkgs.buildNpmPackage (npm // {
  pname = "lightning-tui";
  inherit src npmDeps version;

  doCheck = false;
  npmFlags = [ "--legacy-peer-deps" ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/lib/lightning-tui

    # Single self-contained bundle built by scripts/build.mjs (esbuild).
    cp -r dist $out/lib/lightning-tui/dist

    # package.json kept for "type": "module" resolution on `node dist/entry.js`.
    cp package.json $out/lib/lightning-tui/

    runHook postInstall
  '';
})
