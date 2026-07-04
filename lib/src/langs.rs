#![allow(unused_imports)]
use super::{
    errors::Error,
    paths::{bin_path_aarch, bin_path_x86},
};
use std::{fmt, path::PathBuf, process::Command, str::FromStr};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BenchmarkLanguage {
    Scc,
    SccLin,
}

impl BenchmarkLanguage {
    pub fn all() -> [BenchmarkLanguage; 2] {
        [BenchmarkLanguage::Scc, BenchmarkLanguage::SccLin]
    }

    pub fn from_ext(ext: &str) -> Option<BenchmarkLanguage> {
        match ext {
            "sc" => Some(BenchmarkLanguage::Scc),
            "lin" => Some(BenchmarkLanguage::SccLin),
            _ => None,
        }
    }

    pub fn ext(&self) -> &str {
        match self {
            BenchmarkLanguage::Scc => "sc",
            BenchmarkLanguage::SccLin => "lin",
        }
    }

    pub fn suffix(&self) -> &str {
        match self {
            BenchmarkLanguage::Scc => "scc",
            BenchmarkLanguage::SccLin => "lin",
        }
    }

    pub fn from_suffix(s: &str) -> Result<BenchmarkLanguage, Error> {
        match s.to_lowercase().trim() {
            "scc" => Ok(BenchmarkLanguage::Scc),
            "lin" => Ok(BenchmarkLanguage::SccLin),
            _ => Err(Error::unknown_lang("read from suffix", s)),
        }
    }

    pub fn compile_cmd(&self, source_file: &PathBuf, heap_size: Option<usize>) -> Command {
        let compiler = match self {
            BenchmarkLanguage::Scc => "scc",
            BenchmarkLanguage::SccLin => "scc-lin",
        };

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

impl fmt::Display for BenchmarkLanguage {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            BenchmarkLanguage::Scc => f.write_str("SCC"),
            BenchmarkLanguage::SccLin => f.write_str("SCC-Lin"),
        }
    }
}

impl FromStr for BenchmarkLanguage {
    type Err = Error;
    fn from_str(s: &str) -> Result<BenchmarkLanguage, Self::Err> {
        match s.to_lowercase().trim() {
            "scc" => Ok(BenchmarkLanguage::Scc),
            "scc-lin" => Ok(BenchmarkLanguage::SccLin),
            _ => Err(Error::unknown_lang("Parse Language Name", s)),
        }
    }
}
