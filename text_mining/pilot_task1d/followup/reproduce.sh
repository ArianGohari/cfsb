#!/bin/sh
set -eu
cd "$(dirname "$0")"
# Existing raw responses are reused. A fresh copy without raw/ performs public requests.
python3 pilot.py seeds
python3 pilot.py clarify --name fu --query 'TITLE:"The circadian gene Period2 plays an important role in tumor suppression and DNA damage response in vivo"'
python3 pilot.py clarify --name gery --query 'TITLE:"The circadian gene per1 plays an important role in cell growth and DNA damage control in human cancer cells"'
python3 pilot.py clarify --name matsuo --query 'TITLE:"Control mechanism of the circadian clock for timing of cell division in vivo"'
python3 pilot.py openalex
python3 pilot.py search
python3 pilot.py clarify --name period_cancer --query '(TITLE:"period" AND TITLE:"tumor") AND FIRST_PDATE:[2004-01-01 TO 2014-12-31]'
python3 pilot.py clarify --name cry_cancer --query '(TITLE:"cryptochrome" AND (TITLE:"cancer" OR TITLE:"tumor")) AND FIRST_PDATE:[2004-01-01 TO 2014-12-31]'
python3 pilot.py clarify --name clock_damage --query '(TITLE:"circadian" AND TITLE:"DNA damage") AND FIRST_PDATE:[2004-01-01 TO 2013-12-31]'
python3 pilot.py clarify --name glucocorticoid --query 'DOI:10.1371/journal.pbio.0050078'
python3 pilot.py clarify --name per1_silencing --query 'DOI:10.1158/1078-0432.CCR-06-1730'
python3 pilot.py edges
python3 pilot.py export
python3 validate.py
