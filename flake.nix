{
  description = "Run bash with all dependencies installed";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
    flake-utils.url = "github:numtide/flake-utils";
    scc-main = {
      url = "github:SequentCalculus/sequent-calculus-compiler/main";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    scc-lin = {
      url = "github:SequentCalculus/sequent-calculus-compiler/linear-continuations";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    scc-sf1 = {
      url = "github:SequentCalculus/sequent-calculus-compiler/fc475608a0b2c12d98e50da95287155400d3cd9a";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    scc-sf2 = {
      url = "github:SequentCalculus/sequent-calculus-compiler/8b86954437338419581c3572147a303ccd3a3451";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    scc-sf3 = {
      url = "github:SequentCalculus/sequent-calculus-compiler/b9e35140111beaf20d6603e3f6955d74a2e05965";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    scc-sf4 = {
      url = "github:SequentCalculus/sequent-calculus-compiler/79dd034d844b6952d41b74af7c3d7399e2c7a07d";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = inputs@{ self, nixpkgs, flake-utils, ... }:
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
          (pkgs.writeShellScriptBin "scc-main"
            ''${inputs.scc-main.packages.${system}.default}/bin/scc "$@"'')
          (pkgs.writeShellScriptBin "scc-lin"
            ''${inputs.scc-lin.packages.${system}.default}/bin/scc "$@"'')
          (pkgs.writeShellScriptBin "scc-sf1"
            ''${inputs.scc-sf1.packages.${system}.default}/bin/scc "$@"'')
          (pkgs.writeShellScriptBin "scc-sf2"
            ''${inputs.scc-sf2.packages.${system}.default}/bin/scc "$@"'')
          (pkgs.writeShellScriptBin "scc-sf3"
            ''${inputs.scc-sf3.packages.${system}.default}/bin/scc "$@"'')
          (pkgs.writeShellScriptBin "scc-sf4"
            ''${inputs.scc-sf4.packages.${system}.default}/bin/scc "$@"'')

          #required by rustc
          pkgs.gcc

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
