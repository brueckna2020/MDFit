#!/bin/bash

###Example MDFit command for 4 PD-L1 peptides
###Flag details:
    #Prepared protein file (-p 6PV9_PDL1.mae)
    #Prepared ligand file (-l MDFit_PDL1_Example_Ligands.mae)
    #Custom OPLS directory (-o "/Examples/PDL1/PDL1_oplsdir")
    #100 ns MD (-t 100000)
    #Three repetitions (-r 3)
    #Remove first 100 frames before analysis (--slice_start = 100)
    #Require interaction to exist for 30% of simulation (--analysis_cutoff 0.3)
    #Run with debug (-d)

MDFit -p 6PV9_PDL1.mae -l MDFit_PDL1_Example_Ligands.mae -o "/Examples/PDL1/PDL1_oplsdir" -t 100000 -r 3 --slice_start 100 --analysis_cutoff 0.3 -d
