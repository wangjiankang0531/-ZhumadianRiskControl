"""Rebuild the public business-test QR locally, without an external QR service.
Generator: Project Nayuki QR-Code-generator v1.8.0, MIT; vendored file retains its license.
"""
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'vendor'))
from qrcodegen import QrCode
URL='https://www.joinlinksmart.com/zhumadian/'
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'web/src/home-access-qr.svg');a=p.parse_args()
 q=QrCode.encode_text(URL,QrCode.Ecc.MEDIUM);n=q.get_size();b=4
 cells=''.join(f'M{x+b},{y+b}h1v1h-1z' for y in range(n) for x in range(n) if q.get_module(x,y))
 a.output.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n+8} {n+8}" shape-rendering="crispEdges"><title>驻马店公网业务测试入口</title><rect width="100%" height="100%" fill="white"/><path d="'+cells+'" fill="#07132e"/></svg>',encoding='utf-8')
if __name__=='__main__':main()
