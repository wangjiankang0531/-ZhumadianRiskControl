from pathlib import Path
V=Path(__file__).parent;p=V/'verify_native_personal_workflow_r198_20261103.mjs';s=p.read_text(encoding='utf-8')
old="cases.push({case:label+'-native-home-entry-and-list-without-server-workflow-menu',rows:result.listCount,passed:true});return lists.get(result.path).list;"
new="""cases.push({case:label+'-native-home-entry-and-list-without-server-workflow-menu',rows:result.listCount,passed:true});
 const previous=http.filter(x=>x.path.endsWith(endpoint)).length;
 await send('Page.reload',{ignoreCache:true},session);
 await until(()=>http.filter(x=>x.path.endsWith(endpoint)).length>previous);
 await until(()=>evaluate('location.pathname==='+JSON.stringify(route)+'&&!!document.querySelector(".work-list")'));
 const refreshed=http.filter(x=>x.path.endsWith(endpoint)).at(-1);
 if(refreshed.httpStatus!==200||refreshed.businessCode!==200||!refreshed.listIsArray)throw Error('AUTHENTICATED_PERSONAL_ROUTE_REFRESH_REQUIRED');
 cases.push({case:label+'-normal-browser-refresh-keeps-personal-route-with-missing-menu',passed:true});
 return lists.get(refreshed.path).list;"""
assert s.count(old)==1;s=s.replace(old,new);p.write_text(s,encoding='utf-8');print('ADDED_REAL_PAGE_RELOAD_PERSONAL_ROUTE_REGRESSION')
