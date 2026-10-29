package com.naimat.autotimelinesync;
import org.json.*;
import java.util.*;
/** Rejects duplicate keys, trailing input, nonfinite constants and invalid JSON numbers. */
public final class StrictJson {
 private final String text; private int pos,depth;
 private StrictJson(String t){text=t;}
 public static JSONObject object(String t)throws Exception{
  if(t==null||t.getBytes("UTF-8").length>52428800)throw new Exception("$: JSON exceeds the 50 MiB safety limit.");
  t=t.trim();if(t.startsWith("\uFEFF"))t=t.substring(1).trim();
  if(t.startsWith("```")){int n=t.indexOf('\n');if(n<0||!t.endsWith("```"))throw new Exception("$: incomplete JSON fence.");t=t.substring(n+1,t.length()-3).trim();}
  StrictJson p=new StrictJson(t);Object v=p.value();p.space();if(p.pos!=t.length())p.fail("extra data after JSON object");if(!(v instanceof JSONObject))p.fail("expected one JSON object");return (JSONObject)v;
 }
 private void space(){while(pos<text.length()&&" \r\n\t".indexOf(text.charAt(pos))>=0)pos++;}
 private void fail(String m)throws Exception{throw new Exception("$: invalid JSON at character "+(pos+1)+": "+m);}
 private boolean consume(char c){space();if(pos<text.length()&&text.charAt(pos)==c){pos++;return true;}return false;}
 private String string()throws Exception{space();if(pos>=text.length()||text.charAt(pos++)!='"')fail("expected quoted string");StringBuilder b=new StringBuilder();while(pos<text.length()){char c=text.charAt(pos++);if(c=='"')return b.toString();if(c<32)fail("unescaped control character");if(c=='\\'){if(pos>=text.length())fail("invalid escape");c=text.charAt(pos++);switch(c){case '"':case '\\':case '/':b.append(c);break;case 'b':b.append('\b');break;case 'f':b.append('\f');break;case 'n':b.append('\n');break;case 'r':b.append('\r');break;case 't':b.append('\t');break;case 'u':if(pos+4>text.length())fail("invalid Unicode escape");try{b.append((char)Integer.parseInt(text.substring(pos,pos+4),16));pos+=4;}catch(Exception e){fail("invalid Unicode escape");}break;default:fail("invalid escape");}}else b.append(c);}fail("unterminated string");return "";}
 private Object value()throws Exception{
  space();if(++depth>128)fail("nesting exceeds 128");try{if(pos>=text.length())fail("missing value");char c=text.charAt(pos);if(c=='"')return string();
   if(c=='{'){pos++;JSONObject o=new JSONObject();Set<String> keys=new HashSet<>();if(consume('}'))return o;do{String k=string();if(!keys.add(k))fail("duplicate key "+k);if(!consume(':'))fail("expected colon");o.put(k,value());if(consume('}'))return o;}while(consume(','));fail("expected comma or }");}
   if(c=='['){pos++;JSONArray a=new JSONArray();if(consume(']'))return a;do{a.put(value());if(consume(']'))return a;}while(consume(','));fail("expected comma or ]");}
   for(String s:new String[]{"true","false","null"})if(text.startsWith(s,pos)){pos+=s.length();return s.equals("null")?JSONObject.NULL:Boolean.valueOf(s);}
   int start=pos;while(pos<text.length()&&"0123456789eE+-.".indexOf(text.charAt(pos))>=0)pos++;String n=text.substring(start,pos);
   if(!n.matches("-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?"))fail("invalid value/number");double d=Double.parseDouble(n);if(!Double.isFinite(d))fail("nonfinite number");if(!n.contains(".")&&!n.contains("e")&&!n.contains("E")){try{return Long.valueOf(n);}catch(Exception ignored){}}return d;
  }finally{depth--;}
 }
}
