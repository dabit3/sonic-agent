# nix/web.nix — Sonic Web Dashboard (Vite/React) frontend build
{ pkgs, sonicNpmLib, ... }:
let
  src = ../web;
  npmDeps = pkgs.fetchNpmDeps {
    inherit src;
    hash = "sha256-RZ/zU8EkKAIz3h0g/nBUG7Kzd/B+7RnrXAPlbwIr/C4=";
  };

  npm = sonicNpmLib.mkNpmPassthru { folder = "web"; attr = "web"; pname = "sonic-web"; };

  packageJson = builtins.fromJSON (builtins.readFile (src + "/package.json"));
  version = packageJson.version;
in
pkgs.buildNpmPackage (npm // {
  pname = "sonic-web";
  inherit src npmDeps version;

  doCheck = false;

  buildPhase = ''
    npx tsc -b
    npx vite build --outDir dist
  '';

  installPhase = ''
    runHook preInstall
    cp -r dist $out
    runHook postInstall
  '';
})
