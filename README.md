# MDFit
Python wrapper for high-throughput molecular dynamics. A workflow overview and application of MDFit to a data set of macrocyclic peptides targetting PD-L1 are discussed in _TBD_.[^1]
[^1]: Reference TBD

MDFit currently uses Schrodinger tools. Implementation of alternatives, including open-source tools, are ongoing.
# Prerequisites
MDFit assumes the `$SCHRODINGER` environmental variable has been set. This should point to the current Schrodinger installation. To check if `$SCHRODINGER` has been set correctly, try running: `$SCHRODINGER/run -h`


MDFit attempts to get the current Schrodinger release by reading the `$SCHRODINGER` pathname. For example, if the current release is installed in `/schrodinger/2023-2/`, MDFit will set the release to 2023-2. This value can also be hard-coded in MDFit (line 38) if a different directory naming scheme is used.

The first time MDFit.py is called, a `parameters_TEMPLATE.json` file is generated in the installation directory. Replace `localhost` with your institution's Schrodinger hostnames and rename the file to `parameters.json`. This is required only once and MDFit will always read `parameters.json` to get host information on subsequent runs. General runtime limit guidance:
```
FFBUILDER   7 days
BMIN        12 hours
MULTISIM    12 hours
DESMOND     3 days
ANALYSIS    3 days
```
# Usage
```
$SCHRODINGER/run python3 MDFit.py -h
```
Self-contained example available in `MDFit/Examples/PDL1/`. The following command will run FFBuilder, three repetitions of 100 ns Desmond MD, and MD analysis for Pep-01, Pep-41, Pep-52, and Pep-66. The first 100 frames will be removed from the trajectory before analysis (`--slice_start`) and the cutoff for retaining a protein-ligand interaction is 0.3 (`--analysis_cutoff`).
```
$SCHRODINGER/run python3 MDFit.py -p 6PV9_PDL1.mae -l MDFit_PDL1_Example_Ligands.mae -o "MDFit/Examples/PDL1/PDL1_oplsdir" -t 100000 -r 3 --slice_start 100 --analysis_cutoff 0.3 -d
```
It is strongly encouraged to use the debug flag `-d` for initial MDFit usage. Errors may occur if packages are not where MDFit expects them to be.


# Bugs and Known Errors
+ Schrodinger release relying on installation pathname.
