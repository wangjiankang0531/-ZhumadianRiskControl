package xnby.platform;

import java.lang.reflect.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import javax.servlet.http.*;

/** Copy live request metadata by value; an asynchronous job never delegates getters to a recycled request. */
public final class OriginalAsyncHttpMetadata implements InvocationHandler {
 private final Map<String,List<String>> headers=new TreeMap<String,List<String>>(String.CASE_INSENSITIVE_ORDER);
 private final Map<String,Long> dates=new TreeMap<String,Long>(String.CASE_INSENSITIVE_ORDER);
 private final Map<String,Integer> integers=new TreeMap<String,Integer>(String.CASE_INSENSITIVE_ORDER);
 private final Map<String,Object> scalars=new HashMap<String,Object>();
 private final Map<String,String[]> parameters=new LinkedHashMap<String,String[]>();
 private final Map<String,Object> attributes=new ConcurrentHashMap<String,Object>();
 private final List<Locale> locales=new ArrayList<Locale>();
 private final Cookie[] cookies;private final HttpSession session;
 private static void need(boolean value,String code){if(!value)throw new IllegalStateException(code);}
 public static HttpServletRequest capture(HttpServletRequest source)throws Exception {
  OriginalAsyncHttpMetadata copy=new OriginalAsyncHttpMetadata(source);
  return (HttpServletRequest)Proxy.newProxyInstance(HttpServletRequest.class.getClassLoader(),new Class<?>[]{HttpServletRequest.class},copy);
 }
 private OriginalAsyncHttpMetadata(HttpServletRequest source)throws Exception {
  int bytes=0,count=0;Enumeration<String> names=source.getHeaderNames();
  while(names!=null&&names.hasMoreElements()){
   String name=names.nextElement();need(++count<=128,"ASYNC_METADATA_HEADER_COUNT");List<String> values=new ArrayList<String>();Enumeration<String> all=source.getHeaders(name);
   while(all!=null&&all.hasMoreElements()){String value=all.nextElement();bytes+=name.length()+value.length();need(values.size()<64&&bytes<=32768,"ASYNC_METADATA_HEADER_BOUND");values.add(value);}
   need(!headers.containsKey(name),"ASYNC_METADATA_AMBIGUOUS_HEADER_NAME");headers.put(name,Collections.unmodifiableList(values));
   try{dates.put(name,source.getDateHeader(name));}catch(IllegalArgumentException invalid){}
   try{integers.put(name,source.getIntHeader(name));}catch(NumberFormatException invalid){}
  }
  count=0;bytes=0;
  for(Map.Entry<String,String[]> row:source.getParameterMap().entrySet()){
   need(++count<=256&&row.getValue().length<=64,"ASYNC_METADATA_PARAMETER_COUNT");String[] values=row.getValue().clone();bytes+=row.getKey().length();for(String value:values)bytes+=value==null?0:value.length();need(bytes<=65536,"ASYNC_METADATA_PARAMETER_BOUND");parameters.put(row.getKey(),values);
  }
  Enumeration<String> attrs=source.getAttributeNames();count=0;
  while(attrs!=null&&attrs.hasMoreElements()){String name=attrs.nextElement();need(++count<=256,"ASYNC_METADATA_ATTRIBUTE_COUNT");Object value=source.getAttribute(name);if(value!=null)attributes.put(name,value);}
  String[] methods={"getAuthType","getContextPath","getMethod","getPathInfo","getPathTranslated","getQueryString","getRemoteUser","getRequestedSessionId","getRequestURI","getServletPath","getCharacterEncoding","getContentLength","getContentLengthLong","getContentType","getProtocol","getScheme","getServerName","getServerPort","getRemoteAddr","getRemoteHost","getRemotePort","getLocalName","getLocalAddr","getLocalPort","isSecure","isRequestedSessionIdValid","isRequestedSessionIdFromCookie","isRequestedSessionIdFromURL","isRequestedSessionIdFromUrl","getServletContext","getUserPrincipal","getDispatcherType","getLocale"};
  for(String name:methods)scalars.put(name,HttpServletRequest.class.getMethod(name).invoke(source));
  scalars.put("getRequestURL",source.getRequestURL().toString());Enumeration<Locale> allLocales=source.getLocales();while(allLocales!=null&&allLocales.hasMoreElements()){need(locales.size()<32,"ASYNC_METADATA_LOCALE_BOUND");locales.add(allLocales.nextElement());}
  Cookie[] original=source.getCookies();cookies=cloneCookies(original);session=source.getSession(false);
 }
 private static Cookie[] cloneCookies(Cookie[] source){if(source==null)return null;need(source.length<=128,"ASYNC_METADATA_COOKIE_COUNT");Cookie[] result=new Cookie[source.length];for(int i=0;i<source.length;i++)result[i]=(Cookie)source[i].clone();return result;}
 @Override public Object invoke(Object proxy,Method method,Object[] args)throws Throwable {
  String name=method.getName();
  if(name.equals("toString"))return "AsyncHttpMetadata[redacted]";
  if(name.equals("hashCode"))return System.identityHashCode(proxy);
  if(name.equals("equals"))return proxy==args[0];
  if(name.equals("getHeader")){List<String> values=headers.get((String)args[0]);return values==null||values.isEmpty()?null:values.get(0);}
  if(name.equals("getHeaders")){List<String> values=headers.get((String)args[0]);return Collections.enumeration(values==null?Collections.<String>emptyList():values);}
  if(name.equals("getHeaderNames"))return Collections.enumeration(headers.keySet());
  if(name.equals("getDateHeader")){String key=(String)args[0];if(!headers.containsKey(key))return -1L;if(!dates.containsKey(key))throw new IllegalArgumentException("Invalid date header");return dates.get(key);}
  if(name.equals("getIntHeader")){String key=(String)args[0];if(!headers.containsKey(key))return -1;if(!integers.containsKey(key))throw new NumberFormatException("Invalid integer header");return integers.get(key);}
  if(name.equals("getParameter")){String[] values=parameters.get((String)args[0]);return values==null||values.length==0?null:values[0];}
  if(name.equals("getParameterValues")){String[] values=parameters.get((String)args[0]);return values==null?null:values.clone();}
  if(name.equals("getParameterNames"))return Collections.enumeration(parameters.keySet());
  if(name.equals("getParameterMap")){Map<String,String[]> values=new LinkedHashMap<String,String[]>();for(Map.Entry<String,String[]> row:parameters.entrySet())values.put(row.getKey(),row.getValue().clone());return Collections.unmodifiableMap(values);}
  if(name.equals("getAttribute"))return attributes.get((String)args[0]);
  if(name.equals("getAttributeNames"))return Collections.enumeration(attributes.keySet());
  if(name.equals("setAttribute")){if(args[1]==null)attributes.remove((String)args[0]);else attributes.put((String)args[0],args[1]);return null;}
  if(name.equals("removeAttribute")){attributes.remove((String)args[0]);return null;}
  if(name.equals("getCookies"))return cloneCookies(cookies);
  if(name.equals("getLocales"))return Collections.enumeration(locales);
  if(name.equals("getRequestURL"))return new StringBuffer((String)scalars.get(name));
  if(name.equals("getSession")){if(session!=null||args!=null&&args.length==1&&!((Boolean)args[0]))return session;throw new IllegalStateException("ASYNC_METADATA_CANNOT_CREATE_SESSION_AFTER_RESPONSE");}
  if(name.equals("isUserInRole")&&scalars.get("getUserPrincipal")==null)return false;
  if(name.equals("isAsyncStarted")||name.equals("isAsyncSupported"))return false;
  if(name.equals("setCharacterEncoding")){scalars.put("getCharacterEncoding",args[0]);return null;}
  if(scalars.containsKey(name))return scalars.get(name);
  // Body/response/dispatch operations require a live HTTP exchange. Never fabricate data or consult the recycled request.
  throw new IllegalStateException("ASYNC_HTTP_OPERATION_REQUIRES_LIVE_EXCHANGE:"+name);
 }
}
