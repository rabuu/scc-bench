{
  description = "Run bash with all dependencies installed";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    scc.url = "github:SequentCalculus/sequent-calculus-compiler";
    scc-lin.url = "github:SequentCalculus/sequent-calculus-compiler/linear-continuations";
  };

  outputs = { self, nixpkgs, flake-utils, scc, scc-lin, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        rustPlatform = pkgs.rustPlatform;
        python = pkgs.python312.withPackages (ps: with ps; [
          polars
          pandas
          pyarrow
          numpy
          plotly
          kaleido
          matplotlib
        ]);
        dependencies = [
          #compilers
          pkgs.ocaml
          pkgs.koka
          pkgs.smlnj
          pkgs.mlton
          scc.packages.${system}.default
          (pkgs.writeShellScriptBin "scc-lin"
            ''${scc-lin.packages.${system}.default}/bin/scc "$@"'')
          pkgs.rustc

          #required by rustc
          pkgs.gcc
          #required by ocaml (on MacOS)
          pkgs.clang
          #required by smlnj
          pkgs.gnugrep
          pkgs.gnused
          #required by mlton
          pkgs.coreutils

          #hyperfine
          pkgs.hyperfine
          pkgs.bash

          python
        ];
      in {
        packages = {
          sccBench = pkgs.rustPlatform.buildRustPackage {
            pname = "Sequent-Calculus-Bench";
            version = "0.1.0";
            src = ./.;
            nativeBuildInputs = [ pkgs.makeWrapper pkgs.pkgconf ];
            buildInputs = dependencies ++ [ pkgs.fontconfig pkgs.expat ];
            cargoDeps = rustPlatform.importCargoLock { lockFile = ./Cargo.lock; };
            postFixup = ''
              makeWrapper $out/bin/bench $out/bin/run-bench \
              --set PATH "${pkgs.lib.makeBinPath dependencies}";
              '';
        };
        default=self.packages.${system}.sccBench;
      };

      devShells = {
        sccShell = pkgs.mkShell {
          buildInputs = [ self.packages.${system}.default ];
          packages = dependencies;

          shellHook = ''
            export name=""
            echo "Call 'run-bench' to start benchmarks"
            '';
        };
        default=self.devShells.${system}.sccShell;
      };

      apps = {
        sccApp = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/run-bench";
        };
        default = self.apps.${system}.sccApp;
      };
  }); 
}
