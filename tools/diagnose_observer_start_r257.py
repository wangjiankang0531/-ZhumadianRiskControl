from pathlib import Path
V=Path(__file__).parent
s=(V/'diagnose_observer_start_r255.py').read_text(encoding='utf-8').replace('r123','r127').replace('r255','r257').replace('R255','R257')
exec(compile(s,str(__file__),'exec'))
