# emmtyper - Emm Automatic Isolate Labeller

[![CircleCI](https://circleci.com/gh/MDU-PHL/emmtyper.svg?style=svg)](https://circleci.com/gh/MDU-PHL/emmtyper)
[![Coverage Status](https://coveralls.io/repos/github/MDU-PHL/emmtyper/badge.svg?branch=master)](https://coveralls.io/github/MDU-PHL/emmtyper?branch=master)

## Table of Content

1. [Introduction](#introduction)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Usage](#usage)
	- [Arguments for emmtyper](#arguments-for-emmtyper)
	- [Arguments for Tools in emmtyper](#arguments-for-tools-in-emmtyper)
		- [blastn Options](#blastn-options)
		- [ispcr Options](#ispcr-options)
	- [Example Commands](#example-commands)
5. [Result Format](#result-format)
6. [BLAST or PCR?](#blast-or-pcr)
7. [Contact](#contact)

## Introduction

emmtyper is a command line tool for emm-type classification of Streptococcus pyogenes based on the isolate's whole genome sequence.

The use of emmtyper will follow the dependencies of the tools within its pipeline, namely `blastn` and `ispcr`.

## Requirements

emmtyper needs `blastn` and `ispcr`. As is, there is no way to automatically install both automatically with setup.py.

User (for now) will need to manually install the tools themselves and set them on $PATH for emmtyper to work (emmtyper expected both tools to be on $PATH).

emmtyper requires Python >= 3. It requires Numpy and Scipy, both included in the setup.py.

## Installation

emmtyper uses setup.py for easier installation. Clone the GitHub page for emmtyper, and run setup.py over the command line on the directory where setup.py for emmtyper is located.
The command is:

```sh
$ python3 setup.py install
``` 

You will then be able to use emmtyper by calling `emmtyper` on the command line.

## Usage

emmtyper has 2 branches of usage: direct BLAST, or isPcr followed by BLAST. Product of any of the two pipelines will go through emmtyper's clusterer to derive the type of the isolate.

The basic usage of emmtyper is in the form of:

```sh
emmtyper ... [blast/pcr] ...
```

On `[blast/pcr]`, you are required to choose between `blast` or `pcr` to choose which pipeline you want. The first ellipsis `...` is for emmtyper's arguments. The second ellipsis `...` is for arguments within the tools used in emmtyper; `blastn` for BLAST pathway, and `ispcr` and `blastn` for PCR pathway.

### Arguments for emmtyper
These arguments are required for both of the pipelines:

| Argument | Variable Type | Description |
| ------ | ------ | ------ |
| --query | FASTA | An assembled genome FASTA |
| --db | blast DB | A BLAST database file |

While the optional arguments are:

| Argument | Variable Type | Default | Description |
| ------ | ------ | ------ | ------ |
| -clust_distance | integer | 500 | Distance between clusters to use |
| -output_type | string | short | Output type format. Choose within "short", "verbose", or "visual" |
| -saveIntermediary | boolean | False | On mention, do not remove intermediary files between tools |
| -outFinal | tsv | stdout | File to stream final output |

### Arguments for Tools in emmtyper
#### blastn Options
Options in `blastn` that can be manually changed for both BLAST and PCR pipeline.

| Argument | Variable Type | Default | Description |
| ------ | ------ | ------ | ------ |
| -dust | string | no | Filter query sequence with DUST |
| -perc_identity | integer | 95 | Minimal percent identity of sequence |
| -culling_limit | integer | 5 | Total hits to return in a single position |
| -mismatch | integer | 4 | Threshold number of mismatch to allow in BLAST hit |
| -align_diff | integer | 5 | Threshold for difference between alignment length and subject length in BLAST hit |
| -gap | integer | 2 | Threshold number of gap to allow in BLAST hit |

#### ispcr Options
Options in `ispcr` that can be manually changed for the PCR pipeline. Aside from the optionals, the PCR pipeline has an additional required argument.

| Argument | Variable Type | Description |
| ------ | ------ | ------ |
| --primer | tsv | A tsv file containing primer set in the format "PrimerSetName\tPrimer1Sequence\tPrimer2Sequence" |

| Argument | Variable Type | Default | Description |
| ------ | ------ | ------ | ------ |
| -minPerfect | integer | 15 | Minimum size of perfect match at 3' primer end |
| -minGood | integer | 15 | Minimum size where there must be 2 matches for each mismatch | 
| -maxSize | integer | 4000 | Positive integer value for maximum product length |
| -savePCR | boolean | False | On mention, PCR output file will not be automatically removed | 

Again, you can also manually change the [options in blastn](#blastn-options) within the PCR pipeline.

### Example Commands
```sh
emmtyper --query isolate1.fa --db emm.fasta blast
emmtyper --query *.fa --db emm.fasta pcr --primer emmPrimer.tsv
emmtyper --query *.fa --db blastDB/emm.fasta -saveIntermediary blast -culling_limit 10 -align_diff 10
emmtyper --query Run19Jun/*.fa --db emm.fasta -output_type visual pcr --primer emmPrimer.tsv -maxSize 2000 -mismatch 5
```

## Result Format
emmtyper has three different result formats: `short`, `verbose`, and `visual`.

emmtyper by default produces the `short` five tab-separated values to the command line. You can call `-output_type <option>` to choose the other two result format.

The short result returns: **Isolate name_Number of clusters_Predicted type_Possible imposters_Answer's EMM cluster**

While the verbose result returns: **Isolate name_Number of BLAST hits_Number of clusters_Predicted type_Position in assembly_Possible imposters_Imposters position in assembly_Answer's EMM cluster**,
where the positions are presented in <contig_number>:<position_in_contig>.

The visual result returns an ASCII map of the emm-types in the genome. Types in a single contig are separated with "-", each representing 500bp distance from each other. Types found in different contigs are separated with tab.

The types are presented with flags when something is not right, the possible flags for now being:

| Flag | Description | Additional Information |
| ------ | ------ | ------ |
| * | Suspect Imposter | Types acknowledged in the CDC database as possibly not emm |
| ~ | Imperfect score | Match score below 100% |

Example for all result format:

```
Isolate1	1	EMM65.0	E6
Isolate2	3	EMM4.0	EMM236.3*;EMM156.0*	E1
Isolate3	2	EMM52.1	EMM134.2*	D4

Isolate1	6	1	EMM65.0	5:82168	E6
Isolate2	8	3	EMM4.0	2:104111	EMM236.3*;EMM156.0*	2:102762;2:105504	E1
Isolate3	5	2	EMM52.1	14:10502	EMM134.2*	5:913	D4

Isolate1	EMM65.0
Isolate2	EMM156.0*--EMM4.0--EMM236.3*
Isolate3	EMM52.1	EMM134.2*
```

## BLAST or PCR?

If you are not sure which pipeline to choose from, I recommend using `blast` first, and use `pcr` when you want to check if anything weird is happening in your `blast` result. 

An example problem where this might be useful is when there are too much hits reported by emmtyper. 

An important thing to note is that not all emm-like can be caught in the conventional PCR typing. PCR pipeline here can be used to see which hits would be returned in the setting of a conventional typing. This is however not fail-proof, as in silico PCR fails when the two primers do not align in the same contig. Better assembly would resolve this problem.

## Contact 

Should you want to fill issues or contact me about anything regarding emmtyper, 
you can reach me here or on my email: andre.sutanto.91@gmail.com.
