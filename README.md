# DRACONIS
DRACONIS (**D**esign **R**ule **A**nalysis and **C**hecking **O**f **N**orms in **I**EC & **S**imulink) is a parser 
and analyser of block-based models. 

It performs different types of static analyses for the purpose of 
verifying that design rules have been followed during the implementation.

The tool supports checking of configurable rules in an interactive manner.

## Installation
From the base path, run the following commands to setup all pre-requisites for the project. 
```
pip install -r requirements_development.txt
pushd ./parser && ./regen_parser.sh && popd
```