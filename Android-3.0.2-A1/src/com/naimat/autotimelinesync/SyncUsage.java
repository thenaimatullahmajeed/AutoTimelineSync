package com.naimat.autotimelinesync;
import org.json.*;import java.util.*;

/** Same informational B modes; never changes authored effects or rejects budgets. */
public final class SyncUsage {
 static boolean cut(String s){return s.equals("HARD_CUT")||s.equals("NONE");}
 static void count(JSONObject o,String key)throws Exception{o.put(key,o.optInt(key)+1);}
 public static JSONObject counts(List<String> types,String energy,double frequency)throws Exception{
  int b=types.size(),n=0,f=0,maximum=0;boolean repeated=false,adjacent=false;Map<String,Integer>same=new HashMap<>();
  for(int i=0;i<b;i++){String t=types.get(i);if(!cut(t))n++;if(ATSModel.FANCY.contains(t)){f++;same.put(t,same.getOrDefault(t,0)+1);maximum=Math.max(maximum,same.get(t));}if(i>0){String prev=types.get(i-1);repeated|=prev.equals(t)&&!cut(t);adjacent|=ATSModel.FANCY.contains(prev)&&ATSModel.FANCY.contains(t);}}
  double factor=energy.equals("SUBTLE")?.45:energy.equals("HIGH_ENERGY")?1.7:1;
  int budget=frequency==0?0:Math.max(1,(int)Math.ceil(b*frequency*factor)),standardFancy=Math.min(energy.equals("HIGH_ENERGY")?b/4:3*b/20,budget);
  JSONObject caps=new JSONObject().put("STANDARD",new JSONObject().put("noncut_max",2*b/5).put("fancy_max",standardFancy).put("same_fancy_max",2)).put("RICH",new JSONObject().put("noncut_min",(11*b+19)/20).put("noncut_max",7*b/10).put("fancy_min",(b+4)/5).put("fancy_max",b/4).put("same_fancy_max",3)).put("MAX",new JSONObject().put("noncut_required",b).put("fancy_max",7*b/20).put("same_fancy_max",3));
  JSONArray matches=new JSONArray();if(b>0&&!repeated&&!adjacent){if(n==b&&f<=7*b/20&&maximum<=3)matches.put("MAX");if(n>=(11*b+19)/20&&n<=7*b/10&&f>=(b+4)/5&&f<=b/4&&maximum<=3)matches.put("RICH");if(n<=2*b/5&&f<=standardFancy&&maximum<=2)matches.put("STANDARD");}
  return new JSONObject().put("mode",matches.length()==0?"NONE":matches.getString(0)).put("matching_modes",matches).put("boundaries",b).put("noncuts",n).put("fancy",f).put("same_fancy_maximum",maximum).put("adjacent_fancy",adjacent).put("repeated_adjacent_noncut",repeated).put("generated_director_budget",budget).put("thresholds",caps).put("enforcement","INFO only; never reject or rewrite");
 }
 public static JSONObject utilization(ATSModel m,boolean music)throws Exception{
  List<String>types=new ArrayList<>();JSONObject transitions=new JSONObject(),moments=new JSONObject(),overlays=new JSONObject();int motions=0,looks=0;
  for(int i=0;i<m.scenes.size();i++){ATSModel.Scene s=m.scenes.get(i);if(i>0){types.add(s.transition);count(transitions,s.transition);}if(s.raw.has("motion_config"))motions++;if(s.raw.has("look_override"))looks++;}
  for(JSONObject moment:m.moments)count(moments,moment.optString("type"));for(JSONObject overlay:m.overlays)count(overlays,overlay.optString("type"));
  JSONObject classification=counts(types,m.direction.optString("energy","BALANCED"),m.direction.optDouble("transition_frequency",.15));String numeric=classification.getString("mode");JSONArray issues=new JSONArray();
  if(!m.scenes.get(0).raw.optString("transition").equals("HARD_CUT"))issues.put("HOUSE RULE: scene 001 must explicitly use HARD_CUT.");
  for(int i=0;i<m.scenes.size();i++){ATSModel.Scene s=m.scenes.get(i);String path="$.scenes["+i+"]";if(!s.raw.has("motion")||!s.raw.has("transition"))issues.put(path+": HOUSE RULE requires explicit motion and transition.");
   for(String k:new String[]{"motion_config","transition_config"})if(s.raw.has(k)&&ATSModel.obj(s.raw,k).length()==0)issues.put(path+"."+k+": HOUSE RULE forbids an empty config.");
   if(i>0&&!cut(s.transition)){if(!s.trans.optString("type").equals(s.raw.optString("transition")))issues.put(path+": HOUSE RULE requires matching transition_config.type.");Object value=s.trans.opt("frames");if(!(value instanceof Number)||((Number)value).doubleValue()!=Math.floor(((Number)value).doubleValue())||((Number)value).intValue()<4||((Number)value).intValue()>30)issues.put(path+": HOUSE RULE requires explicit integer frames from 4 to 30.");int minimum=(int)Math.ceil(Math.max(4,Math.ceil(.12*m.fps))/.45);ATSModel.Scene previous=m.scenes.get(i-1);if(Math.min(s.last-s.first,previous.last-previous.first)<minimum)issues.put(path+": HOUSE RULE non-cut cannot fit both neighboring scenes.");}
   String requested=s.trans.optString("type",s.raw.optString("transition","HARD_CUT"));if(i>0&&!cut(requested)&&cut(s.transition))issues.put(path+": requested non-cut fell back to a cut.");
  }
  classification.put("numeric_mode",numeric).put("house_rule_issues",issues).put("editorial_checks","Story relevance and whether a beat is fast need author review; the app does not infer them.");if(issues.length()>0)classification.put("mode","NONE");
  int cues=AudioEngine.effects(m).size();JSONArray unused=new JSONArray();LinkedHashMap<String,Boolean>used=new LinkedHashMap<>();
  used.put("overlays",!m.overlays.isEmpty());used.put("DATE_CARD",moments.optInt("DATE_CARD")>0);used.put("CIRCLE",moments.optInt("CIRCLE")>0);used.put("PHOTO_NOTE",overlays.optInt("PHOTO_NOTE")>0);used.put("motion_config",motions>0);used.put("look_override",looks>0);used.put("style",m.style.length()>0);used.put("audio",m.audio.length()>0);used.put("ending",m.ending.length()>0);used.put("SFX",cues>0);JSONObject finish=ATSModel.obj(m.direction,"finish");used.put("finish",finish.optDouble("grain")!=0||finish.optDouble("vignette")!=0||finish.optDouble("contrast")!=0);used.put("music",music);
  List<String>missing=new ArrayList<>();for(Map.Entry<String,Boolean>e:used.entrySet())if(!e.getValue()){unused.put(e.getKey());missing.add(e.getKey());}
  String mode=classification.getString("mode");int b=types.size(),n=classification.getInt("noncuts"),f=classification.getInt("fancy");String line="Mode "+mode+": "+n+" non-cut of "+b+", "+f+" fancy, "+moments.optInt("DATE_CARD")+" date cards, "+cues+" sound cues, "+m.overlays.size()+" overlays, features unused: "+(missing.isEmpty()?"none":String.join(", ",missing))+".";
  JSONArray unusedTransitions=new JSONArray();for(String t:new TreeSet<>(ATSModel.TRANSITIONS))if(!transitions.has(t))unusedTransitions.put(t);
  return new JSONObject().put("contract_id",SyncSupport.CONTRACT).put("scene_count",m.scenes.size()).put("boundaries",b).put("transitions_by_type",transitions).put("noncut_boundaries",n).put("noncut_share",b==0?0:n/(double)b).put("fancy_boundaries",f).put("moments_by_type",moments).put("sfx_cue_count",cues).put("overlays_by_type",overlays).put("scenes_using_motion_config",motions).put("scenes_using_look_override",looks).put("supported_features_not_used",unused).put("unused_transition_enums",unusedTransitions).put("classification",classification).put("mode",mode).put("utilization_line",line).put("warnings",new JSONArray(m.notices)).put("note","Actual native applied effects and cues; first scene excluded. House modes are information, never acceptance rules.");
 }
}
