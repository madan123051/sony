{
  inputs = {
    # nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable"; #! if commented out, it uses my pinned
  };
  outputs = inputs@{ self, nixpkgs, flake-utils, ... }:
    let
      supportedSystems = [ "x86_64-linux" "x86_64-darwin" "aarch64-linux" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
      # pkgs-s = forAllSystems (system: import nixpkgs { inherit system; });
      pkgs-s = system: import nixpkgs { inherit system; };
      py_deps = pyPackages: builtins.map (x: pyPackages.${x}) [
        "asn1crypto"
        "pyaxmlparser"
        "certifi"
        "pycparser"
        "pycryptodomex"
        "pyinstaller"
        "setuptools"
        "pyusb"
        "pyyaml"
        "tlslite-ng"
        "tkinter"
        "wrapPython"
      ];
      mkWrappedPkg = { name, pkgs }: pkgs.stdenv.mkDerivation {
        name = name;#
        src = ./.;
        buildInputs = [ pkgs.python311 ] ++ (py_deps pkgs.python311Packages);
        installPhase = ''
          mkdir -p $out/bin
          mkdir -p $out/deps
          cp -r $src/* $out/deps
        '';
        postFixup = ''
          wrapProgram $out/deps/pmca-${name}.py --prefix PYTHONPATH : $PYTHONPATH
          ln -s $out/deps/pmca-${name}.py $out/bin/${name}
        '';
      };
      # mkWrappedPkgs = 
      #   tpkgs: 
      #   pkgs: 
      #   builtins.map (x: mkWrappedPkg { name = x; inherit pkgs; }) tpkgs;

    in {
      packages = forAllSystems (system: let pkgs = pkgs-s system; in rec {
        console = mkWrappedPkg { name = "console"; inherit pkgs; };
        gui = mkWrappedPkg { name = "gui"; inherit pkgs; };
        default = gui;
      });
      devShells = forAllSystems (system: let pkgs = pkgs-s system; in {
        default = pkgs.mkShell {
          buildInputs = [ pkgs.python311 ] ++ (py_deps pkgs.python311Packages);
        };
      });
    };
}
