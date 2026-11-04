#![allow(unused_imports)]
use super::{
    errors::Error,
    paths::{bin_path_aarch, bin_path_x86},
};
use std::{fmt, path::PathBuf, process::Command, str::FromStr};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BenchmarkCompiler {
    suffix: String,
}

impl BenchmarkCompiler {
    pub fn all() -> Vec<Self> {
        vec![
            Self {
                suffix: "main".to_string(),
            },
            Self {
                suffix: "lin".to_string(),
            },
            Self {
                suffix: "sf1".to_string(),
            },
            Self {
                suffix: "sf2".to_string(),
            },
            Self {
                suffix: "sf3".to_string(),
            },
            Self {
                suffix: "sf4".to_string(),
            },
        ]
    }

    pub fn from_ext(ext: &str) -> Vec<BenchmarkCompiler> {
        match ext {
            "sc" => Self::all(),
            _ => vec![],
        }
    }

    pub fn ext(&self) -> &str {
        "sc"
    }

    pub fn suffix(&self) -> &str {
        &self.suffix
    }

    pub fn from_suffix(s: &str) -> BenchmarkCompiler {
        Self {
            suffix: s.to_lowercase().trim().to_string(),
        }
    }

    pub fn compile_cmd(&self, source_file: &PathBuf, heap_size: Option<usize>) -> Command {
        let compiler = format!("scc-{}", self.suffix);

        let mut cmd = Command::new(compiler);
        cmd.arg("codegen");
        cmd.arg(source_file);
        #[cfg(target_arch = "x86_64")]
        cmd.arg("x86-64");
        #[cfg(target_arch = "aarch64")]
        cmd.arg("aarch64");
        if let Some(hs) = heap_size {
            cmd.arg("--heap-size");
            cmd.arg(format!("{hs}"));
        }
        cmd
    }
}

impl fmt::Display for BenchmarkCompiler {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "SCC-{}", self.suffix)
    }
}

impl FromStr for BenchmarkCompiler {
    type Err = Error;
    fn from_str(s: &str) -> Result<BenchmarkCompiler, Self::Err> {
        match s.to_lowercase().trim().split_once('-') {
            Some(("scc", suffix)) => Ok(BenchmarkCompiler {
                suffix: suffix.to_string(),
            }),
            _ => Err(Error::unknown_lang("Parse Language Name", s)),
        }
    }
}
