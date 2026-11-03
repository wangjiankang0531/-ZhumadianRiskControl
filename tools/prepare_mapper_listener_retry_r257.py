from pathlib import Path
import ast,subprocess,sys
V=Path(__file__).parent
java=(V/'OwnMapperRegistrationObservationR256.java').read_text(encoding='utf-8').replace('R256','R257')
p=V/'OwnMapperRegistrationObservationR257.java';assert not p.exists();p.write_text(java,encoding='utf-8')
s=(V/'prepare_mapper_observation_suite_r256.py').read_text(encoding='utf-8').replace('r256','r257').replace('R256','R257').replace('r125','r127').replace('r126','r128').replace('${application}','${APP}')
s=s.replace('import argparse,hashlib,json,subprocess,os\n','import argparse,hashlib,json,subprocess,os,re\n')
needle="arguments[cpindex]+=';'+newjar"
assert s.count(needle)==1
s=s.replace(needle,needle+";assert set(re.findall(r'\\\\$\\\\{([^}]+)\\\\}',arguments[cpindex]))<={'APP','BUSINESS_RUN','PLATFORM_RUN','PLATFORM_DATA'},'UNKNOWN_CLASSPATH_TOKEN_REFUSED'")
p=V/'prepare_mapper_observation_suite_r257.py';assert not p.exists();ast.parse(s);p.write_text(s,encoding='utf-8')
s=(V/'prepare_mapper_fixture_r256.py').read_text(encoding='utf-8').replace('r256','r257').replace('r125','r127').replace('r126','r128')
p2=V/'prepare_mapper_fixture_r257.py';assert not p2.exists();ast.parse(s);p2.write_text(s,encoding='utf-8')
r=subprocess.run([sys.executable,str(p)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0,r.stderr.decode('utf-8',errors='replace')[-1000:];print(r.stdout.decode())
