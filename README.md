# ICEfinder 2.0

ICEfinder 2.0 - Detecting Integrative and Conjugative Elements in Bacteria.

> [!NOTE]
> This repo contains a copy of https://tool2-mml.sjtu.edu.cn/ICEberg3/Download.html.

## Welcome to use ICEfinder local version

> [!Tip]
> ICEfinder also has a web version, you can access it easily by https://tool2-mml.sjtu.edu.cn/ICEberg3/ICEfinder.php.

## Installation

The local version of ICEfinder2 has been tested in CentOS Linux release 7.7.1908.

This local clone was also tested on Ubuntu 20.04 with the patches documented at the end of this README.

To install ICEfinder2, just download the file 'ICEfinder2_linux.tar.gz' from the 'Download' [webpage](https://tool2-mml.sjtu.edu.cn/ICEberg3/Download.html) and then decompress it:

```bash
$ tar -xvzf ICEfinder2_linux.tar.gz
```

ICEfinder2 has multiple programs dependency: 

Hmmer, version 3.1 or greater
BLAST, version 2.10.1+ or greater
Kraken, version 2.0.9-beta or greater (For Metagenome)
seqkit, version 0.12.0
prodigal, V2.6.3
prokka, V1.14.6
defensefinder, v1.0.9
macsyfinder, 2.0rc6
And you need to specify the installation path for the software in the config.ini file.

ICEfinder2 also relies on Python library dependencies:
Biopython
ete3

For a local Python environment without Conda:
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

Or with `uv`:
```bash
uv venv .venv
uv pip install --python .venv/bin/python --prerelease=allow -r requirements.txt
```

To run ICEfinder with the local virtual environment without activating it:
```bash
./run.sh -i example/input_demo/CP003200.1.gb -t Single
```

Convenience wrappers:
```bash
./run-single.sh example/input_demo/CP003200.1.gb
./run-metagenome.sh example/input_demo/SRS146999.fna
```

The wrappers keep the type fixed, but the input file is required:
```bash
./run-single.sh path/to/genome.gb
./run-metagenome.sh path/to/metagenome.fna
```

To test and get familiar with the ICEfinder, you can test the demo files we provide in the 'example/input_demo' directory,
```bash
run `python3 ICEfinder2.py -i example/input_demo/file -t Single/Metagenome`. You can also compare your output in the 'result'
```
to the results in the directory 'example/result_demo'.

> [!NOTE]
> DefenseFinder and MacSyFinder currently support the specified versions only. We will be conducting version updates later.

## Input data

At present, ICEfinder2 accepts the bacterial genome sequences in the GenBank or FASTA format. 
And You can input a single bacterial sequence (in either FASTA or GenBank format) or multiple metagenome sequences (in FASTA format) for analysis.

Example of list file format:
CP003200.1.gb
NC_000964.3.gb
SRS146999.fna

> [!NOTE]
> A. These three GenBank files are the example for the detection of G- T4SS-type ICEs, G+ T4SS-type ICEs and metagenome ICEs respectively.
> B. For Genbank format, only accept the standard gbk files that contain single contig with full sequence.

## OUTPUT
The output files in the directory 'result/' may include:

### `*_info.json`

The summary json file about the input genome.

```json
 {
     "JobID": "CP003200.1",
     "Submission date": "Fri Oct 1 00:18:44 2023",
     "Sequence name": "CP003200.1",
     "Length": "5333942 bp",
     "GC Content": "57.48 %"
 }
```

### `*_ICEsum.json`

The summary json file about the putative ICE/IME.
```json
 {
     "id": "1",
     "region": "Region1",
     "location": "3433540..3495705",
     "length": "62166",
     "gc": "52.46",
     "type": "T4SS-type ICE",
     "detail": "CP003200.1_ICE4"
    }
```

### `*_ICE*_info.json`

Detailed feature information for each ICE

```json
 {
     "Type": "T4SS-type ICE",
     "Location (nt)": "3433540..3495705",
     "Length (bp)": "62166",
     "GC Content (%)": "52.46",
     "oriT seq": "CCGATTAGGCGCGACCAACCCCTTTAAAGCAGCGTTCCCATTTTTTCGAGCTTGCGAAGAAAAAATAGGCTAAACGCGCGTCTTAAAGGGGTTGGTCGCGCGTAGCGTGCGACGGTGTGCCGCC",
     "DRs": "attL:3433540..3433556(CAGTCAGAGGAGCCAA)  attR:3495689..3495705(CAGTCAGAGGAGCCAA)",
     "Relaxase Type": "MOBC",
     "Mating pair formation systems": "typeT",
     "Close to tRNA": "tRNA-Asn (3433479..3433555) [+]"
 }
```

### `*_ICE*.html, *_ICE*_gene.json`

Detailed gene structure information for each ICE along with web-based visualization results.
```json
 [
    {
        "gene": "KPHS_34550",
        "pos": "3428319..3428709 [-], 391",
        "prod": "hypothetical protein",
        "featu": "Flank"
    },

  ....

    {
        "gene": "KPHS_35020",
        "pos": "3500665..3502288 [-], 1624",
        "prod": "putative lysophospholipase",
        "featu": "Flank"
    }
 ]
```

## Contact

If you have any question for ICEfinder 2.0, please feel free to contact the authors:

- hyou@sjtu.edu.cn
- m.wang@sjtu.edu.cn

## Local Patches

The following patches were applied on top of the original upstream code to make the local clone runnable on this machine:

- Switched the Python entrypoint shebangs and CLI usage examples to `python3`.
Reason: the original scripts pointed to hard-coded interpreter paths that do not exist here, and the system `python` is Python 2.7.

- Added `script/bio_compat.py` and replaced direct use of `Bio.SeqUtils.GC` with a compatibility helper based on `gc_fraction` when available.
Reason: recent Biopython versions removed `GC`, which caused the program to fail at import time.

- Replaced the deprecated Biopython BLAST command wrappers in `script/function.py` with direct `subprocess` calls.
Reason: this removes dependency on deprecated `Bio.Blast.Applications` wrappers and keeps BLAST invocation explicit.

- Fixed the startup bug in `ICEfinder2.py` where missing `tmp/fasta` caused the code to create `tmp/gbk` a second time instead of creating `tmp/fasta`.
Reason: the original code could fail immediately with `FileExistsError` before starting the analysis.

- Fixed the symbiosis BLAST call in `script/function.py` to use the protein FASTA input with `blastp` instead of the nucleotide FASTA input.
Reason: the original code passed an `.ffn` file to `blastp`, which is inconsistent and can produce invalid results.

- Updated the `defense-finder` invocation in `script/function.py` to run via `subprocess` with `.venv/bin` added to `PATH`.
Reason: `defense-finder` calls `macsyfinder` internally, and the original environment did not expose that executable when ICEfinder was launched via the local virtualenv.
