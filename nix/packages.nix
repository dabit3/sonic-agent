# nix/packages.nix — Sonic Agent package built with uv2nix
{ inputs, ... }:
{
  perSystem =
    { pkgs, inputs', ... }:
    let
      sonicAgent = pkgs.callPackage ./sonic-agent.nix {
        inherit (inputs) uv2nix pyproject-nix pyproject-build-systems;
        npm-lockfile-fix = inputs'.npm-lockfile-fix.packages.default;
        # Only embed clean revs — dirtyRev doesn't represent any upstream
        # commit, so comparing it would always claim "update available".
        rev = inputs.self.rev or null;
      };
    in
    {
      packages = {
        default = sonicAgent;
        tui = sonicAgent.sonicTui;
        web = sonicAgent.sonicWeb;

        fix-lockfiles = sonicAgent.sonicNpmLib.mkFixLockfiles {
          packages = [ sonicAgent.sonicTui sonicAgent.sonicWeb ];
        };
      };
    };
}
