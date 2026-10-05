import React,{useEffect,useMemo,useState} from "react";
import {createRoot} from "react-dom/client";
import {MapContainer,TileLayer,Marker,Popup} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "./styles.css";

const API="http://127.0.0.1:8000";
const tokenKey="rentmatch_token";

function api(path,options={}){
  const token=localStorage.getItem(tokenKey);
  const headers={...(token?{Authorization:`Bearer ${token}`}:{})};
  if(!(options.body instanceof FormData)) headers["Content-Type"]="application/json";
  return fetch(API+path,{...options,headers:{...headers,...(options.headers||{})}});
}
function pinIcon(){return L.divIcon({className:"custom-pin",html:"<span>🏠</span>",iconSize:[34,34],iconAnchor:[17,30]});}

function Auth({onAuth}){
  const [mode,setMode]=useState("login"),[name,setName]=useState(""),[email,setEmail]=useState(""),[password,setPassword]=useState(""),[role,setRole]=useState("tenant"),[error,setError]=useState(""),[loading,setLoading]=useState(false);
  async function submit(e){e.preventDefault();setError("");setLoading(true);try{
    const path=mode==="login"?"/api/auth/login":"/api/auth/register";
    const body=mode==="login"?{email,password}:{name,email,password,role};
    const r=await api(path,{method:"POST",body:JSON.stringify(body)});const d=await r.json();if(!r.ok)throw new Error(d.detail||"Request failed");
    localStorage.setItem(tokenKey,d.token);onAuth(d.user);
  }catch(e){setError(e.message)}finally{setLoading(false)}}
  return <div className="auth-page"><div className="auth-card">
    <div className="logo">🏠 <b>RentMatch</b> <span>AI</span></div>
    <div className="auth-copy"><span className="eyebrow">INTELLIGENT RENTAL DISCOVERY</span><h1>Find a home that <span>fits you.</span></h1><p>Search homes using natural language, compare match scores, save properties, and connect with owners.</p></div>
    <div className="tabs"><button className={mode==="login"?"active":""} onClick={()=>setMode("login")}>Login</button><button className={mode==="register"?"active":""} onClick={()=>setMode("register")}>Create account</button></div>
    <form onSubmit={submit}>{mode==="register"&&<><input value={name} onChange={e=>setName(e.target.value)} placeholder="Full name" required/><div className="role-choice"><button type="button" className={role==="tenant"?"selected":""} onClick={()=>setRole("tenant")}>🏠 Find a home</button><button type="button" className={role==="owner"?"selected":""} onClick={()=>setRole("owner")}>🏢 List my property</button></div></>}<input type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="Email address" required/><input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Password (6+ characters)" required/><button className="primary wide" disabled={loading}>{loading?"Please wait…":mode==="login"?"Login →":"Create account →"}</button></form>
    {error&&<div className="error">{error}</div>}
    <div className="auth-note">Create an account to save properties, keep search history, and manage your own listings.</div>
  </div></div>
}

function PropertyCard({p,onOpen,saved,onToggle}){
  return <article className="property-card"><div className="photo-wrap"><img src={API+p.image} onError={e=>{e.currentTarget.src=p.image}}/><span className="score">{p.match_score??"—"}% match</span><button className={`heart ${saved?"saved":""}`} onClick={()=>onToggle(p.id)}>{saved?"♥":"♡"}</button></div><div className="card-body"><div className="area">{p.area} · {p.distance_km?p.distance_km+" km":"New listing"}</div><h3>{p.title}</h3><div className="facts"><b>₹{p.rent.toLocaleString("en-IN")}</b><span>{p.bhk} BHK</span><span>{p.bathrooms} Bath</span></div><div className="amenities">{p.amenities.slice(0,4).map(a=><span key={a}>{a}</span>)}</div><button className="outline wide" onClick={()=>onOpen(p)}>View full details</button></div></article>
}

function Details({p,onClose}){
  const [active,setActive]=useState(0);if(!p)return null;const gallery=p.gallery?.length?p.gallery:[p.image];
  return <div className="modal-backdrop" onClick={onClose}><div className="modal" onClick={e=>e.stopPropagation()}><button className="close" onClick={onClose}>×</button><div className="gallery"><img className="modal-img" src={API+gallery[active]} onError={e=>{e.currentTarget.src=gallery[active]}}/>{gallery.length>1&&<div className="thumbs">{gallery.map((g,i)=><button className={i===active?"thumb active":"thumb"} key={g+i} onClick={()=>setActive(i)}><img src={API+g} onError={e=>{e.currentTarget.src=g}}/></button>)}</div>}</div><div className="modal-content"><span className="eyebrow">{p.area} · AVAILABLE</span><h2>{p.title}</h2><p>{p.description}</p><div className="detail-grid"><div><b>₹{p.rent.toLocaleString("en-IN")}</b><small>Monthly rent</small></div><div><b>{p.bhk} BHK</b><small>Bedrooms</small></div><div><b>{p.bathrooms}</b><small>Bathrooms</small></div><div><b>{p.distance_km||"—"} km</b><small>Distance</small></div></div><h3>Features & amenities</h3><div className="amenities">{p.amenities.map(a=><span key={a}>{a}</span>)}{p.parking&&<span>Parking</span>}{p.wifi&&<span>Wi-Fi</span>}{p.furnished&&<span>Furnished</span>}</div>{p.match_score!==undefined&&<div className="explain"><b>{p.match_score}% match</b><div>{p.reasons?.map(([kind,text],i)=><span key={i} className={kind}>{kind==="yes"?"✓":kind==="no"?"•":"i"} {text}</span>)}</div></div>}<div className="owner"><div><b>Owner: {p.owner.name}</b><p>{p.owner.phone}<br/>{p.owner.email}</p></div></div></div></div></div>
}

function MapView({properties,onOpen}){
  const center=properties.length?[properties.reduce((a,p)=>a+p.lat,0)/properties.length,properties.reduce((a,p)=>a+p.lng,0)/properties.length]:[22.5,79.0];
  const spread=properties.length?Math.max(...properties.map(p=>p.lat))-Math.min(...properties.map(p=>p.lat)):0;
  const zoom=spread>8?5:spread>3?7:11;
  return <MapContainer center={center} zoom={zoom} scrollWheelZoom className="leaflet-map"><TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>{properties.map(p=><Marker key={p.id} position={[p.lat,p.lng]} icon={pinIcon()}><Popup><b>{p.title}</b><br/>{p.area}<br/>₹{p.rent.toLocaleString("en-IN")} / month<br/><button className="map-open" onClick={()=>onOpen(p)}>View details</button></Popup></Marker>)}</MapContainer>
}

function OwnerPortal({user,areas,onCreated}){
  const [form,setForm]=useState({title:"",area:"",rent:"",bhk:"2",bathrooms:"1",phone:"",amenities:"Lift, Security",description:"",furnished:false,parking:false,wifi:false});
  const [files,setFiles]=useState([]),[mine,setMine]=useState([]),[msg,setMsg]=useState(""),[error,setError]=useState(""),[loading,setLoading]=useState(false);
  async function loadMine(){const r=await api("/api/owner/properties");if(r.ok)setMine((await r.json()).properties)}
  useEffect(()=>{if(user.role==="owner")loadMine()},[user.role]);
  function change(k,v){setForm(x=>({...x,[k]:v}))}
  async function submit(e){e.preventDefault();setError("");setMsg("");if(!files.length){setError("Please upload at least one flat photo.");return}setLoading(true);try{
    const fd=new FormData();Object.entries(form).forEach(([k,v])=>fd.append(k,String(v)));files.forEach(f=>fd.append("files",f));
    const r=await api("/api/owner/properties",{method:"POST",body:fd});const d=await r.json();if(!r.ok)throw new Error(d.detail||"Could not publish property");
    setMsg("Property published successfully. It is now visible in rental search.");setForm({title:"",area:"",rent:"",bhk:"2",bathrooms:"1",phone:"",amenities:"Lift, Security",description:"",furnished:false,parking:false,wifi:false});setFiles([]);await loadMine();onCreated(d.property);
  }catch(e){setError(e.message)}finally{setLoading(false)}}
  async function remove(id){if(!confirm("Remove this listing?"))return;const r=await api(`/api/owner/properties/${id}`,{method:"DELETE"});if(r.ok)loadMine()}
  if(user.role!=="owner")return <section className="page-section"><span className="eyebrow">OWNER PORTAL</span><h1>List your property</h1><div className="owner-gate"><div>🏢</div><h2>Owner account required</h2><p>Log out and create an account with <b>List my property</b> selected. Then this separate owner page lets you upload photos and publish listings.</p></div></section>;
  return <section className="page-section owner-page"><span className="eyebrow">OWNER PORTAL</span><h1>Publish a rental property</h1><p className="lead">Add your flat details, upload photos, and make the property searchable for renters.</p>{msg&&<div className="success">✓ {msg}</div>}{error&&<div className="error">{error}</div>}
    <form className="owner-form" onSubmit={submit}><div className="form-section"><h2>Property details</h2><div className="form-grid"><label>Property title<input value={form.title} onChange={e=>change("title",e.target.value)} placeholder="e.g. Sunrise Residency 2 BHK" required/></label><label>Area<select value={form.area} onChange={e=>change("area",e.target.value)} required><option value="">Choose area</option>{areas.map(a=><option key={a}>{a}</option>)}</select></label><label>Monthly rent<input type="number" min="1000" value={form.rent} onChange={e=>change("rent",e.target.value)} placeholder="18000" required/></label><label>BHK<select value={form.bhk} onChange={e=>change("bhk",e.target.value)}><option>1</option><option>2</option><option>3</option><option>4</option></select></label><label>Bathrooms<input type="number" min="1" value={form.bathrooms} onChange={e=>change("bathrooms",e.target.value)} required/></label><label>Owner phone<input value={form.phone} onChange={e=>change("phone",e.target.value)} placeholder="+91 9XXXXXXXXX" required/></label></div><label>Description<textarea value={form.description} onChange={e=>change("description",e.target.value)} placeholder="Describe the flat, nearby transport, floor, sunlight, water supply, etc." required/></label><label>Amenities <span className="muted">comma separated</span><input value={form.amenities} onChange={e=>change("amenities",e.target.value)} placeholder="Lift, Balcony, Security"/></label><div className="checks"><label><input type="checkbox" checked={form.furnished} onChange={e=>change("furnished",e.target.checked)}/> Furnished</label><label><input type="checkbox" checked={form.parking} onChange={e=>change("parking",e.target.checked)}/> Parking</label><label><input type="checkbox" checked={form.wifi} onChange={e=>change("wifi",e.target.checked)}/> Wi-Fi</label></div></div>
      <div className="form-section"><h2>Flat photos</h2><p className="muted">Upload up to 8 JPG, PNG, WEBP or GIF photos. The first photo becomes the cover image.</p><input className="file-input" type="file" accept="image/jpeg,image/png,image/webp,image/gif" multiple onChange={e=>setFiles(Array.from(e.target.files||[]))}/>{files.length>0&&<div className="file-list">{files.map(f=><span key={f.name}>{f.name}</span>)}</div>}<button className="primary" disabled={loading}>{loading?"Publishing…":"Publish property →"}</button></div>
    </form>
    <div className="my-listings"><div className="section-title"><div><span className="eyebrow">MY LISTINGS</span><h2>Properties you have published</h2></div><span>{mine.length} listings</span></div>{mine.length?<div className="grid">{mine.map(p=><article className="mini-listing" key={p.id}><img src={API+p.image}/><div><b>{p.title}</b><span>{p.area} · ₹{p.rent.toLocaleString("en-IN")}</span><button onClick={()=>remove(p.id)}>Remove listing</button></div></article>)}</div>:<div className="empty compact"><div>🏠</div><h2>No listings yet</h2></div>}</div>
  </section>
}

function App({user,onLogout}){
  const [query,setQuery]=useState(""),[results,setResults]=useState([]),[requirements,setRequirements]=useState({}),[agent,setAgent]=useState(null),[loading,setLoading]=useState(false),[error,setError]=useState(""),[selected,setSelected]=useState(null),[view,setView]=useState("search"),[favorites,setFavorites]=useState([]),[history,setHistory]=useState([]),[areas,setAreas]=useState([]),[area,setArea]=useState(""),[maxRent,setMaxRent]=useState(""),[bhk,setBhk]=useState(""),[sort,setSort]=useState("match"),[allProperties,setAllProperties]=useState([]);
  async function refreshSaved(){const [f,h]=await Promise.all([api("/api/favorites"),api("/api/history")]);if(f.ok)setFavorites((await f.json()).properties);if(h.ok)setHistory((await h.json()).history)}
  async function loadAll(){const [p,a]=await Promise.all([api("/api/properties"),api("/api/areas")]);if(p.ok)setAllProperties((await p.json()).properties);if(a.ok)setAreas((await a.json()).areas)}
  useEffect(()=>{loadAll();refreshSaved()},[]);
  async function search(q=query){if(!q.trim())return;setLoading(true);setError("");try{const r=await api("/api/search",{method:"POST",body:JSON.stringify({query:q})});const d=await r.json();if(!r.ok)throw new Error(d.detail||"Search failed");setResults(d.results);setRequirements(d.requirements);setAgent(d.agent);setArea("");setMaxRent("");setBhk("");setView("search");await refreshSaved()}catch(e){setError(e.message)}finally{setLoading(false)}}
  async function toggleFav(id){const saved=favorites.some(p=>p.id===id);const r=await api(saved?`/api/favorites/${id}`:"/api/favorites",{method:saved?"DELETE":"POST",...(saved?{}:{body:JSON.stringify({property_id:id})})});if(r.ok)refreshSaved()}
  const source=results.length?results:allProperties;
  const displayed=useMemo(()=>{let x=[...source];if(area)x=x.filter(p=>p.area===area);if(maxRent)x=x.filter(p=>p.rent<=+maxRent);if(bhk)x=x.filter(p=>p.bhk===+bhk);if(sort==="rent")x.sort((a,b)=>a.rent-b.rent);if(sort==="distance")x.sort((a,b)=>(a.distance_km||99)-(b.distance_km||99));if(sort==="match")x.sort((a,b)=>(b.match_score||0)-(a.match_score||0));return x},[source,area,maxRent,bhk,sort]);
  const savedIds=new Set(favorites.map(p=>p.id));
  const req=[requirements.area&&`📍 ${requirements.area}`,requirements.bhk&&`🛏 ${requirements.bhk} BHK`,requirements.budget&&`💰 ≤ ₹${requirements.budget.toLocaleString("en-IN")}`,requirements.parking&&"🚗 Parking",requirements.wifi&&"📶 Wi-Fi",requirements.furnished&&"🛋 Furnished"].filter(Boolean);
  return <div><header className="header"><div className="logo">🏠 <b>RentMatch</b> <span>AI</span></div><nav><button className={view==="search"?"nav-active":""} onClick={()=>setView("search")}>Explore</button><button className={view==="favorites"?"nav-active":""} onClick={()=>setView("favorites")}>Saved ({favorites.length})</button><button className={view==="history"?"nav-active":""} onClick={()=>setView("history")}>History</button><button className={view==="owner"?"nav-active":""} onClick={()=>setView("owner")}>Owner Portal</button></nav><div className="user"><span>Hi, {user.name}</span><button onClick={onLogout}>Logout</button></div></header>
  <main>{view==="search"&&<><section className="hero"><div><span className="eyebrow">FAI • AI AGENT • HEURISTIC SEARCH</span><h1>Find a rental that <span>actually matches.</span></h1><p>Search across properties across India. Mention a city, locality, budget, BHK or amenity and the AI agent applies explicit requirements as hard constraints before ranking.</p></div><div className="search-panel"><textarea value={query} onChange={e=>setQuery(e.target.value)} onKeyDown={e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();search()}}} placeholder="Example: 2 BHK in Mumbai under ₹30,000 with parking and Wi-Fi"/><button className="primary" onClick={()=>search()} disabled={loading}>{loading?"AI agent working…":"Find matching flats →"}</button></div><div className="quick"><span>Try:</span>{["2 BHK in Mumbai under 30000 with parking and Wi-Fi","1 BHK in Bengaluru below 20000","furnished 2 BHK in Pune under 22000"].map(q=><button key={q} onClick={()=>{setQuery(q);search(q)}}>{q}</button>)}</div></section>
  {error&&<div className="error">{error}</div>}{agent&&<div className="agent-panel"><div><b>🤖 {agent.name}</b><p>AI provider: <strong>{agent.ai_provider}</strong></p></div><div className="steps">{agent.tools_used.map(t=><span key={t}>✓ {t}</span>)}</div></div>}
  <section className="toolbar"><div><b>{displayed.length}</b> properties {req.length>0&&<div className="chips">{req.map(x=><span key={x}>{x}</span>)}</div>}</div><div className="filters"><select value={area} onChange={e=>setArea(e.target.value)}><option value="">All India</option>{areas.map(a=><option key={a}>{a}</option>)}</select><input type="number" placeholder="Max rent" value={maxRent} onChange={e=>setMaxRent(e.target.value)}/><select value={bhk} onChange={e=>setBhk(e.target.value)}><option value="">Any BHK</option><option value="1">1 BHK</option><option value="2">2 BHK</option><option value="3">3 BHK</option><option value="4">4 BHK</option></select><select value={sort} onChange={e=>setSort(e.target.value)}><option value="match">Best match</option><option value="rent">Lowest rent</option><option value="distance">Nearest</option></select></div></section>
  {requirements.area&&<div className="strict">📍 <b>Location constraint:</b> results below are restricted to <b>{requirements.area}</b>. Other locations are not mixed into this search.</div>}
  <section className="map-section"><div className="section-title"><div><span className="eyebrow">LOCATION VIEW</span><h2>Properties on the map</h2></div><span>{displayed.length} shown</span></div><MapView properties={displayed} onOpen={setSelected}/></section>
  {displayed.length?<div className="grid">{displayed.map(p=><PropertyCard key={p.id} p={p} saved={savedIds.has(p.id)} onToggle={toggleFav} onOpen={setSelected}/>)}</div>:<section className="empty"><div>🏠</div><h2>No property matches the selected requirements</h2><p>Try a wider budget, another BHK, or another area.</p></section>}</>}
  {view==="favorites"&&<section className="page-section"><span className="eyebrow">YOUR COLLECTION</span><h1>Saved properties</h1>{favorites.length?<div className="grid">{favorites.map(p=><PropertyCard key={p.id} p={p} saved onToggle={toggleFav} onOpen={setSelected}/>)}</div>:<div className="empty"><div>♥</div><h2>No saved properties yet</h2><p>Use the heart button on any property to save it.</p></div>}</section>}
  {view==="history"&&<section className="page-section"><span className="eyebrow">YOUR ACTIVITY</span><h1>Search history</h1>{history.length?<div className="history-list">{history.map(h=><button key={h.id} onClick={()=>{setQuery(h.query);search(h.query)}}><span>🔎</span><div><b>{h.query}</b><small>{new Date(h.created_at+"Z").toLocaleString()}</small></div><span>→</span></button>)}</div>:<div className="empty"><div>🕘</div><h2>No searches yet</h2></div>}</section>}
  {view==="owner"&&<OwnerPortal user={user} areas={areas} onCreated={()=>{loadAll();setView("search")}}/>}
  </main><footer>RentMatch AI · Intelligent Rental Discovery · React + FastAPI + SQLite + Gemini</footer><Details p={selected} onClose={()=>setSelected(null)}/></div>
}

function Root(){const [user,setUser]=useState(null);useEffect(()=>{const t=localStorage.getItem(tokenKey);if(t)api("/api/auth/me").then(r=>r.ok?r.json():null).then(d=>d&&setUser(d.user)).catch(()=>{})},[]);function logout(){localStorage.removeItem(tokenKey);setUser(null)}return user?<App user={user} onLogout={logout}/>:<Auth onAuth={setUser}/>}
createRoot(document.getElementById("root")).render(<Root/>);
