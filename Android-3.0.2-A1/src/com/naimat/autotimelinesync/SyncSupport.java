package com.naimat.autotimelinesync;
import android.content.*;import org.json.*;import java.io.*;import java.util.*;

/** Additive diagnostics: the native production parser remains the import oracle. */
public final class SyncSupport {
 public static final String VERSION="3.0.2-A1 Android",CONTRACT="ATS_SYNC_2026-10-B";
 public static final String HEADER="ATS_PACKAGE_V2 correction request. Fix only the paths below and return one complete corrected JSON object. Preserve all other fields.";
 public static final String COLUMNS="path | rule | value | expected | severity";
 public static final String RTL="creator caption layout is left to right; multiword right-to-left order will be wrong";
 private static JSONObject schema,coverage;
 public static String asset(Context c,String file)throws Exception{try(InputStream in=c.getAssets().open(file);ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[]b=new byte[16384];int n;while((n=in.read(b))!=-1)out.write(b,0,n);return out.toString("UTF-8");}}
 static synchronized JSONObject schema(Context c)throws Exception{if(schema==null)schema=new JSONObject(asset(c,"sync-schema.json"));return schema;}
 public static final class Report {
  public final JSONArray diagnostics=new JSONArray();public ATSModel model;
  public boolean valid(){for(int i=0;i<diagnostics.length();i++)if(diagnostics.optJSONObject(i).optString("severity").equals("ERROR"))return false;return true;}
  public void add(String path,String rule,Object value,String expected,String severity){
   for(int i=0;i<diagnostics.length();i++){JSONObject d=diagnostics.optJSONObject(i);if(d.optString("path").equals(path)&&d.optString("severity").equals(severity))return;}
   try{diagnostics.put(new JSONObject().put("path",path).put("rule",rule).put("value",value==null?JSONObject.NULL:value).put("expected",expected).put("severity",severity));}catch(Exception ignored){}
  }
  public String copy(){StringBuilder b=new StringBuilder(HEADER).append('\n').append(COLUMNS);for(int i=0;i<diagnostics.length();i++){JSONObject d=diagnostics.optJSONObject(i);b.append('\n').append(cell(d.optString("path"))).append(" | ").append(cell(d.optString("rule"))).append(" | ").append(cell(jsonValue(d.opt("value")))).append(" | ").append(cell(d.optString("expected"))).append(" | ").append(d.optString("severity"));}return b.toString();}
  static String jsonValue(Object value){String s=new JSONArray().put(value).toString();return s.substring(1,s.length()-1);}
  static String cell(String s){return s.replace("\r","\\r").replace("\n","\\n").replace("|","\\u007c");}
 }
 private static boolean contains(JSONArray a,Object value){if(a==null)return false;for(int i=0;i<a.length();i++)if(Objects.equals(a.opt(i),value))return true;return false;}
 private static void inspect(Object value,String path,JSONObject fields,Report r)throws Exception{
  String template=path.replaceAll("\\[\\d+\\]","[]");if(template.startsWith("$.moments"))return;
  JSONObject f=fields.optJSONObject(template);String type=f==null?"":f.optString("type");
  if(f!=null){
   boolean bad=(type.equals("object")&&!(value instanceof JSONObject))||(type.equals("array")&&!(value instanceof JSONArray))||((type.equals("string")||type.equals("enum"))&&!(value instanceof String))||(type.equals("boolean")&&!(value instanceof Boolean))||((type.equals("number")||type.equals("integer"))&&!(value instanceof Number));
   if(bad){r.add(path,"type",value,"expected "+type,"ERROR");return;}
   if(type.equals("enum")&&!contains(f.optJSONArray("allowed"),value))r.add(path,"enum",value,"must be one of "+f.optJSONArray("allowed"),"ERROR");
   if(f.has("constant")&&!Objects.equals(value,f.opt("constant")))r.add(path,"constant",value,"expected "+f.opt("constant"),"ERROR");
   if(value instanceof Number){double n=((Number)value).doubleValue();boolean integer=type.equals("integer")||f.opt("type") instanceof JSONArray;
    if(!Double.isFinite(n)||(integer&&n!=Math.floor(n))||!f.isNull("minimum")&&n<f.optDouble("minimum")||!f.isNull("maximum")&&n>f.optDouble("maximum")){
     String message=path.equals("$.style.seed")?"must be an integer between 0 and 2147483647":"must be a "+(integer?"integer":"number")+" between "+f.opt("minimum")+" and "+f.opt("maximum");
     r.add(path,"range",value,message,"ERROR");
    }
   }else if(f.opt("type") instanceof JSONArray&&!contains(f.optJSONArray("accepted_strings"),value))r.add(path,"variant",value,"expected AUTO or integer 1 through 9","ERROR");
   if(value instanceof JSONObject){JSONObject o=(JSONObject)value;JSONArray required=f.optJSONArray("required"),allowed=f.optJSONArray("allowed");
    if(required!=null)for(int i=0;i<required.length();i++){String k=required.getString(i);if(!o.has(k))r.add(path+"."+k,"required",null,"required field is missing","ERROR");}
    if(allowed!=null){Iterator<String> keys=o.keys();while(keys.hasNext()){String k=keys.next();if(!contains(allowed,k))r.add(path+"."+k,"field",o.opt(k),"unsupported field; remove it","ERROR");}}
   }
  }
  if(value instanceof JSONObject){JSONObject o=(JSONObject)value;Iterator<String> k=o.keys();while(k.hasNext()){String key=k.next();inspect(o.opt(key),path+"."+key,fields,r);}}
  else if(value instanceof JSONArray){JSONArray a=(JSONArray)value;for(int i=0;i<a.length();i++)inspect(a.opt(i),path+"["+i+"]",fields,r);}
 }
 public static Report validate(Context c,String content){Report r=new Report();JSONObject j;
  try{j=StrictJson.object(content);}catch(Exception e){r.add("$","json_syntax",null,e.getMessage(),"ERROR");return r;}
  try{
   inspect(j,"$",schema(c).getJSONObject("fields"),r);
   for(String group:new String[]{"scenes","captions"}){JSONArray a=j.optJSONArray(group);if(a!=null)for(int i=0;i<a.length();i++){JSONObject o=a.optJSONObject(i);String expected=String.format(Locale.ROOT,"%03d",i+1);if(o!=null&&!expected.equals(o.optString("id")))r.add("$."+group+"["+i+"].id","sequential_id",o.opt("id"),expected,"ERROR");}}
   JSONObject cs=ATSModel.obj(j,"caption_style");String preset=cs.optString("preset","Minimal Cinematic");
   if(cs.has("animation")&&Arrays.asList(ATSModel.PRESETS).subList(0,6).contains(preset))r.add("$.caption_style.animation","product_policy",cs.opt("animation"),"this creator preset has a fixed animation; remove animation.","ERROR");
   try{r.model=ATSModel.parse(content);AudioEngine.effects(r.model);for(String notice:r.model.notices){int colon=notice.indexOf(" skipped:");if(colon>=0)r.add(notice.substring(0,colon),"optional_moment",null,notice,"SKIP");else r.add("$.scenes","render_clamp",null,notice,"WARN");}}
   catch(Exception e){String message=e.getMessage()==null?e.toString():e.getMessage();int k=message.indexOf(':');String p=message.startsWith("$")&&k>0?message.substring(0,k):"$";r.add(p,"production_import",at(j,p),k>0&&p.startsWith("$")?message.substring(k+1).trim():message,"ERROR");r.model=null;}
   fontWarnings(c,j,r);
  }catch(Exception e){r.add("$","diagnostic_internal",null,e.toString(),"WARN");}
  return r;
 }
 public static Object at(JSONObject j,String path){try{Object o=j;for(String token:path.substring(1).replace("[",".").replace("]","").split("\\.")){if(token.isEmpty())continue;o=o instanceof JSONObject?((JSONObject)o).opt(token):((JSONArray)o).opt(Integer.parseInt(token));}return o;}catch(Exception e){return null;}}
 public static void fontWarnings(Context c,JSONObject j,Report r)throws Exception{
  JSONObject cs=ATSModel.obj(j,"caption_style");String preset=cs.optString("preset","Minimal Cinematic"),font=cs.optString("font","Inter");StringBuilder text=new StringBuilder();JSONArray captions=j.optJSONArray("captions");if(captions!=null)for(int i=0;i<captions.length();i++){JSONObject q=captions.optJSONObject(i);if(q!=null)text.append(q.optString("text")).append(' ');}
  boolean creator=Arrays.asList(ATSModel.PRESETS).subList(0,6).contains(preset);
  if(creator&&text.toString().matches("(?s).*[\\u0590-\\u06ff\\u0750-\\u077f\\u08a0-\\u08ff\\ufb1d-\\ufdff\\ufe70-\\ufeff].*"))r.add("$.caption_style.preset","creator_rtl",preset,RTL,"WARN");
  if(coverage==null)coverage=new JSONObject(asset(c,"native-font-coverage.json"));JSONObject primary=coverage.optJSONObject(font);String glyphs=primary==null?"":primary.optString("glyphs");boolean urdu=text.toString().matches("(?s).*[ٹڈڑںےھہگچپژ].*");boolean hindi=false,arabic=false;
  for(int i=0;i<text.length();i++){char ch=text.charAt(i);if(glyphs.indexOf(ch)>=0)continue;if(ch>=0x0900&&ch<=0x097f)hindi=true;if(ch>=0x0600&&ch<=0x06ff||ch>=0x0750&&ch<=0x077f||ch>=0x08a0&&ch<=0x08ff)arabic=true;}
  if(hindi||arabic){String script=hindi?"Hindi":urdu?"Urdu":"Arabic",recommended=hindi?"Poppins":urdu?"Noto Nastaliq Urdu":"DejaVu Sans";r.add("$.caption_style.font","script_font",font,font+" lacks native glyphs for some "+script+" characters; recommend "+recommended+". Font fallback may render them; layout is not certified.","WARN");}
 }
 public static void copy(Context c,String label,String value){ClipData data=ClipData.newPlainText(label,value);if(value.length()>10000){android.os.PersistableBundle extras=new android.os.PersistableBundle();extras.putBoolean("android.content.extra.IS_SENSITIVE",true);data.getDescription().setExtras(extras);}((ClipboardManager)c.getSystemService(Context.CLIPBOARD_SERVICE)).setPrimaryClip(data);}
}
