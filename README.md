# emmtyper - Emm Automatic Isolate Labeller

[![CI](https://github.com/MDU-PHL/emmtyper/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/MDU-PHL/emmtyper/actions/workflows/unit-tests.yml)
[![Coverage Status](https://coveralls.io/repos/github/MDU-PHL/emmtyper/badge.svg?branch=master)](https://coveralls.io/github/MDU-PHL/emmtyper?branch=master) ![PyPI - Implementation](https://img.shields.io/pypi/implementation/emmtyper) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/emmtyper) ![PyPI](https://img.shields.io/pypi/v/emmtyper) ![PyPI - License](https://img.shields.io/pypi/l/emmtyper) ![PyPI - Wheel](https://img.shields.io/pypi/wheel/emmtyper) ![Conda](https://img.shields.io/conda/pn/bioconda/emmtyper?label=bioconda) ![PyPI - Downloads](https://img.shields.io/pypi/dm/emmtyper) ![PyPI - Status](https://img.shields.io/pypi/status/emmtyper) ![GitHub issues](https://img.shields.io/github/issues-raw/MDU-PHL/emmtyper)

## Table of Content

- [emmtyper - Emm Automatic Isolate Labeller](#emmtyper---emm-automatic-isolate-labeller)
  - [Table of Content](#table-of-content)
  - [Background](#background)
    - [Inner workings](#inner-workings)
  - [Requirements](#requirements)
  - [Installation](#installation)
    - [Brew](#brew)
    - [Conda](#conda)
  - [Usage](#usage)
    - [Example Commands](#example-commands)
  - [Result Format](#result-format)
    - [Short format](#short-format)
    - [Verbose format](#verbose-format)
    - [Visual format](#visual-format)
    - [Tags](#tags)
    - [Example outputs](#example-outputs)
  - [BLAST or PCR?](#blast-or-pcr)
  - [Validation data](#validation-data)
  - [Authors](#authors)
  - [Maintainer](#maintainer)
  - [Issues](#issues)
  - [References](#references)

## Background

`emmtyper` is a command line tool for emm-typing of _Streptococcus pyogenes_ using a _de novo_ or complete assembly.

By default, we use the U.S. Centers for Disease Control and Prevention trimmed emm subtype database,
which can be found [here](https://www2a.cdc.gov/ncidod/biotech/strepblast.asp).
The database is curated by Dr. Velusamy Srinivasan. We take this opportunity to thank Dr. Srinivasan for his work.

The tool has two basic modes:

* `blast`: In this mode the contigs are blasted against the trimmed FASTA database curated by the CDC.
* `pcr`: In this mode, first an _in silico_ PCR is done on the contigs using the `isPCR` tool (Kuhn et al. 2013). The resulting fragments are then blasted against the trimmed FASTA database curated by the CDC. Two sets of primers are provided for the user to choose from: 1. The canonical CDC primers used for **conventional** PCR (Whatmore and Kehoe 1994); 2. the primers described by Frost et al. 2020. This last set uses the forward primers of Whatmore and Kehoe (1994), but provide a re-designed reverse primer. There is also the option of the user providing their own primer set in the format required by the `isPCR` tool.

### Inner workings

The difficulty in performing M-typing is that there is a single gene of interest (`emm`), but two other homologue genes (`enn` and `mrp`), often referred to as `emm-like`. The homologue genes may or may not occur in the isolate of interest. When performing `emm-typing` from an assembly, we can distinguish betweeen one or more clusters of matches on the contigs. The best match for each of the clusters identified is then parsed from the BLAST results. Where possible, we try to distinguish between matches to the `emm` gene, and matches to one of the `emm-like` genes.

Possible arrangments:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_emm_

---->>>>>>>----

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_mrp_&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_emm_&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_enn_

---->>>>>>----->>>>>>------>>>>>>-----

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_emm_&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_enn_

----->>>>>>------>>>>>>-----

## Requirements

- `blastn` ≥ 2.6 (tested on 2.9)
- `isPcr`
- `python` ≥ 3.6

## Installation

### Brew

```bash
brew install python blast ispcr
pip3 install emmtyper
emmtyper --help
```

### Conda

```bash
conda install -c conda-forge -c bioconda -c defaults emmtyper
```

## Usage

`emmtyper` has two workflows: directly BLASTing the contigs against the DB, or using `isPcr` to generate an _in silico_ PCR product that is then BLASTed against the DB. The BLAST results go through `emmtyper`'s business logic to distinguish between `emm` and `emm-like` alleles and derive the isoolate M-type.

The basic usage of emmtyper is in the form of:

```bash
emmtyper [options] contig1 contig2 ... contigN
```

All the available options can be printed to the console with `emmtyper --help`. Options passed on to `blast` are tagged with `[BLAST]`, and those for `isPcr` are tagged with `[isPcr]`.

```bash
Usage: emmtyper [OPTIONS] [FASTA]...

  Welcome to emmtyper.

  Usage:

  emmtyper *.fasta

Options:
  --version                       Show the version and exit.
  -w, --workflow [blast|pcr]      Choose workflow  [default: blast]
  -db, --blast_db TEXT            Path to EMM BLAST DB  [default:
                                  /path/to/emmtyper/db/emm.fna]
  -k, --keep                      Keep BLAST and isPcr output files.
                                  [default: False]
  -d, --cluster-distance INTEGER  Distance between cluster of matches to
                                  consider as different clusters.  [default:
                                  500]
  -o, --output TEXT               Output stream. Path to file for output to a
                                  file.  [default: stdout]
  -f, --output-format [short|verbose|visual]
                                  Output format.
  --dust [yes|no|level window linker]
                                  [BLAST] Filter query sequence with DUST.
                                  [default: no]
  --percent-identity INTEGER      [BLAST] Minimal percent identity of
                                  sequence.  [default: 95]
  --culling-limit INTEGER         [BLAST] Total hits to return in a position.
                                  [default: 5]
  --mismatch INTEGER              [BLAST] Threshold for number of mismatch to
                                  allow in BLAST hit.  [default: 4]
  --align-diff INTEGER            [BLAST] Threshold for difference between
                                  alignment length and subject length in BLAST
                                  hit.  [default: 5]
  --gap INTEGER                   [BLAST] Threshold gap to allow in BLAST hit.
                                  [default: 2]
  --blast-path TEXT               [BLAST] Specify full path to blastn
                                  executable.
  --pcr-primers [cdc|frost]       [isPcr] Primer set to use (either canonical
                                  CDC or Frost et al. 2020).  [default: cdc]
  --primer-db TEXT                [isPcr] PCR primer. Text file with 3
                                  columns: Name, Forward Primer, Reverse
                                  Primer. This options overrides --pcr-
                                  primers.
  --min-perfect INTEGER           [isPcr] Minimum size of perfect match at 3\'
                                  primer end.  [default: 15]
  --min-good INTEGER              [isPcr] Minimum size where there must be 2
                                  matches for each mismatch.  [default: 15]
  --max-size INTEGER              [isPcr] Maximum size of PCR product.
                                  [default: 2000] 
  --ispcr-path TEXT               [isPcr] Specify full path to isPcr
                                  executable.
  --help                          Show this message and exit.
```

Most of these options are self explanatory. The two expections are:

1. `--workflow`: choose between a `blast` only workflow, or a _in silico_ PCR followed by `blast` workflow. See below for more information.
2. `--clust_distance` defines the minimum distance between clusters of matched sequences on the contigs to generate separate `emm-type` calls for each clusters. Clusters of matches that are within the minimum `clust-distance` are treated as a single location match.
3. `--output_type` demonstrated below.

### Example Commands

```bash
# basic call using the blast workflow for a single contig file
emmtyper isolate1.fa
# basic call using the pcr workflow for all the .fa files in a folder
emmtyper -w pcr *.fa
# basic call changing some of the options for blast
emmtyper --keep --culling_limit 10 --align_diff 10 *.fa
# call using the pcr workflow changing some of the isPcr options and
# using the visual output format - this will run the with the CDC canonical
# primers
emmtyper -w pcr --output-format visual --max-size 2000 --mismatch 5 *.fa

# same as above, but now with the Frost et al. 2020 primers.
emmtyper -w pcr --output-format visual --max-size 2000 --mismatch 5 --pcr-primers frost *.fa
```

## Result Format

### Short format

emmtyper has three different result formats: `short`, `verbose`, and `visual`.

emmtyper by default produces the `short` version. This consists of five values in tab-separated format printed to stdout.

The values are:

- Isolate name
- Number of clusters: should be between 1 and 3, larger values could indicate contamination
- Predicted `emm-type`
- Possible `emm-like` alleles (semi-colon separated list)
- EMM cluster: Functional grouping of EMM types into 48 clusters

### Verbose format

The verbose result returns:

- Isolate name
- Number of BLAST hits
- Number of clusters: should be between 1 and 3, larger values could indicate contamination
- Predicted `emm-type`
- Position(s) `emm-like` alleles in the assembly
- Possible `emm-like` alleles (semi-colon separated list)
- `emm-like` position(s) in assembly
- EMM cluster: Functional grouping of EMM types into 48 clusters

The positions in the assembly are presented in the following format `<contig_number>:<position_in_contig>`.

### Visual format

The visual result returns an ASCII map of the `emm` and, if found any `emm-alleles`, in the genome. Alleles on a single contig are separated by "-", with each "-" representing 500bp. Alleles found on different contigs are separated with tab.

### Tags

The alleles can be tagged with a suffix character to indicate different possibilities:

| Tag | Description        | Additional Information                                    |
| --- | ------------------ | --------------------------------------------------------- |
| \*  | Suspect `emm-like` | Allele flagged in the CDC database as possibly `emm-like` |
| ~   | Imperfect score    | Match score below 100%                                    |

### Example outputs

Example for all result format:

Short format:

```
Isolate1	1	EMM65.0		E6
Isolate2	3	EMM4.0	EMM236.3*;EMM156.0*	E1
Isolate3	2	EMM52.1	EMM134.2*	D4
```

Verbose format:

```
Isolate1	6	1	EMM65.0	5:82168	E6
Isolate2	8	3	EMM4.0	2:104111	EMM236.3*;EMM156.0*	2:102762;2:105504	E1
Isolate3	5	2	EMM52.1	14:10502	EMM134.2*	5:913	D4
```

Visual format:

```
Isolate1	EMM65.0
Isolate2	EMM156.0*--EMM4.0--EMM236.3*
Isolate3	EMM52.1	EMM134.2*
```

## BLAST or PCR?

If you are not sure which pipeline to choose from, we recommend using `blast` first. The `blast` workflow is fast and works well with assemblies. You can then use the `pcr` mode if you wish to perform some troubleshooting.

For example, the `pcr` workflow might be useful when troubleshooting isolates for which emmtyper has reported more than 3 clusteres and/or too many alleles.

An important thing to note is that not all `emm-like` alleles can be identified by using by PCR typing. The `pcr` workflow can be used to test which hits would be returned if carrying out conventional M-typing using PCR. However, the workflow is not foolproof, as _in silico_ PCR will fail when one or both primers do not align in the same contig (i.e., the allele is broken across two or more contigs) or there are mutations in the primer sites. In the former case, this might be an indication of poor sequence coverage or contamination.

## Validation data

We compared `emmtyper` against `Sanger` sequencing data and PHE's tool [`emm-typing-tool`](https://github.com/phe-bioinformatics/emm-typing-tool).

You can check out the validation comparison go to out binder:

[![badge](https://img.shields.io/badge/launch-binder-579ACA.svg?logo=data:image/png;base64,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)](https://mybinder.org/v2/gh/MDU-PHL/emmtyper/946ddb74e7ce92654567630bd5787430d5945451)

## Authors

- Andre Tan
- Torsten Seemann
- Kristy Horan
- Jake Lacey
- Himal Shrestha
- Raquel Cooper
- Anders Gon&ccedil;alves da Silva

## Acknowledgements
The codebase for `emmtyper` was primarly written by Andre Tan as part of his Master's
Degree in Bioinformatics. Torsten Seemann, Deborah Williamson, and Anders Gon&ccedil;alves da Silva provided supervision and assistance.

Hannah Frost contributed with EMM clustering by suggesting we incorporate it in to the code, and providing the necessary information to do so and test it.

Validation was conducted within MDU-Bioinformatics `emmtyper`.

## Maintainer

The code is actively maintained by MDU Bioinformatics Team.

Contact the principal maintainer at MDU-Bioinformatics@unimelb.edu.au.

## Issues

Please post bug reports, questions, suggestions in the [Issues](https://github.com/MDU-PHL/emmtyper/issues) section.

## References

Frost, H. R., Davies, M. R., Velusamy, S., Delforge, V., Erhart, A., Darboe, S., Steer, A., Walker, M. J., Beall, B., Botteaux, A., & Smeesters, P. R. (2020). Updated emm-typing protocol for Streptococcus pyogenes. Clinical Microbiology and Infection: The Official Publication of the European Society of Clinical Microbiology and Infectious Diseases, 26(7), 946.e5–e946.e8.

Kuhn, R. M., Haussler, D., & Kent, W. J. (2013). The UCSC genome browser and associated tools. Briefings in Bioinformatics, 14(2), 144–161.

Whatmore, A. M., & Kehoe, M. A. (1994). Horizontal gene transfer in the evolution of group A streptococcal emm-like genes: gene mosaics and variation in Vir regulons. Molecular Microbiology, 11(2), 363–374.
