#!/bin/sh
set -eu
cd "$(dirname "$0")"
python3 fulltext.py fetch gaddameedhi_epmc https://www.ebi.ac.uk/europepmc/webservices/rest/PMC3466558/fullTextXML
python3 fulltext.py fetch missing_ids 'https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/?ids=16061665,17332281&idtype=pmid&format=json'
python3 fulltext.py fetch ozturk_epmc https://www.ebi.ac.uk/europepmc/webservices/rest/PMC2634797/fullTextXML
python3 fulltext.py fetch dickmeis_epmc https://www.ebi.ac.uk/europepmc/webservices/rest/PMC1828142/fullTextXML
python3 fulltext.py fetch gaddameedhi_bioc https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/PMC3466558/unicode
python3 fulltext.py fetch ozturk_bioc https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/PMC2634797/unicode
python3 fulltext.py fetch priority_efetch 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=3466558,2634797&retmode=xml'
python3 fulltext.py text dickmeis_epmc
python3 verify_fulltext.py
