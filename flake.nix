{
  description = "ClearThread - Local-first Facebook/Messenger relationship analysis";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    nixvim.url = "github:nix-community/nixvim";
  };

  outputs = { self, nixpkgs, flake-utils, nixvim }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        python3 = pkgs.python312;
        python = python3.withPackages (ps: with ps; [
          # Core data processing
          sqlite-utils
          aiosqlite
          pycryptodome
          PyYAML
          pydantic
          pydantic-settings
          python-dateutil
          zstandard

          # AI/ML
          torch
          transformers
          sentence-transformers
          numpy
          scipy
          faiss-cpu
          hnswlib

          # HTTP/API
          httpx

          # UI
          tauri

          # PDF generation
          reportlab
          markdown

          # Image processing
          Pillow
          opencv

          # Utilities
          click
          rich
          tqdm

          # Dev dependencies
          pytest
          pytest-asyncio
          pytest-cov
          ruff
          black
          mypy
        ]);

        # CUDA support (NVIDIA)
        cudaPackages = pkgs.cudaPackages;

        # GPU libraries
        gpuLibs = with pkgs; [
          cudaPackages.cudatoolkit
          cudaPackages.cudnn
          libGL
          libglib
        ];

        # Tauri dependencies
        tauriDeps = with pkgs; [
          webkitgtk_4_1
          librsvg
          glib-networking
          nss
          at-spi2-atk
          atk
          pango
          cairo
          gdk-pixbuf
        ];

      in
      {
        packages = {
          clearthread = python.pkgs.buildPythonPackage {
            pname = "clearthread";
            version = "0.1.0";
            src = ..;

            nativeBuildInputs = with python.pkgs; [
              hatchling
              pkg-config
            ];

            buildInputs = with python.pkgs; [
              sqlite-utils
              aiosqlite
              pycryptodome
              PyYAML
              torch
              transformers
              sentence-transformers
              numpy
              scipy
              faiss-cpu
              hnswlib
              httpx
              pydantic
              pydantic-settings
              reportlab
              markdown
              Pillow
              opencv
              click
              rich
              tqdm
            ] ++ gpuLibs ++ tauriDeps;

            doCheck = true;
            checkPhase = ''
              pytest tests/ -v
            '';
          };

          default = self.packages.${system}.clearthread;
        };

        devShells.default = pkgs.mkShell {
          name = "clearthread-dev";

          buildInputs = with python.pkgs; [
            python3
            clearthread
            pytest
            pytest-asyncio
            pytest-cov
            ruff
            black
            mypy
            httpx
            pydantic
          ] ++ gpuLibs ++ tauriDeps ++ [
            pkgs.curl
            pkgs.git
            pkgs.nodejs
            pkgs.yarn
            pkgs.tauri-cli
          ];

          # CUDA environment
          LD_LIBRARY_PATH = "${pkgs.cudaPackages.cudatoolkit}/lib:${pkgs.lib.makeLibraryPath gpuLibs}";

          # Nix environment
          NIX_PATH = pkgs.lib.mkForce pkgs.stdenv.cc.cc.lib.meta.nixPath;

          shellHook = ''
            export CLEARTHREAD_DATA_DIR=$PWD/data
            export CLEARTHREAD_MODEL_DIR=$PWD/models
            export PYTHONPATH=$PWD/src:$PYTHONPATH
            echo "ClearThread dev shell ready"
            echo "Python: $(python --version)"
            echo "PyTorch: $(python -c 'import torch; print(torch.__version__)')"
            echo "CUDA available: $(python -c 'import torch; print(torch.cuda.is_available())')"
          '';
        };

        # NixOS package
        nixosModules.default = { config, lib, pkgs, ... }:
          let
            cfg = config.programs.clearthread;
          in
          {
            options.programs.clearthread = {
              enable = lib.mkEnableOption "ClearThread";
              package = lib.mkOption {
                type = lib.types.package;
                default = self.packages.${system}.clearthread;
                description = "ClearThread package";
              };
              dataDir = lib.mkOption {
                type = lib.types.path;
                default = "/var/lib/clearthread";
                description = "Data directory";
              };
              gpuBackend = lib.mkOption {
                type = lib.types.enum [ "cuda" "mps" "rocm" "cpu" ];
                default = "cuda";
                description = "GPU backend";
              };
            };

            config = lib.mkIf cfg.enable {
              programs.nvidia.open = true;

              environment.systemPackages = [ cfg.package ];

              services.ollama = {
                enable = true;
                models = "/var/lib/clearthread/models/ollama";
              };

              systemd.services.clearthread = {
                description = "ClearThread Desktop Application";
                wantedBy = [ "multi-user.target" ];
                after = [ "network.target" "ollama.service" ];
                environment = {
                  CLEARTHREAD_DATA_DIR = cfg.dataDir;
                  GPU_BACKEND = cfg.gpuBackend;
                };
                serviceConfig = {
                  ExecStart = "${cfg.package}/bin/clearthread serve";
                  Restart = "always";
                };
              };
            };
          };
      });
}
