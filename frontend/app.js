import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

let currentView = 'mission'; // Track the current page: 'mission' | 'terrain' | 'optimization'

const $=id=>document.getElementById(id); const API='http://127.0.0.1:8000';
const sites=[
 {name:'Connecting Ridge',lat:-89.30,lon:125.00,score:82,solar:79,earth:91,slope:5.9, demFile: 'connecting_ridge.tif'},
 {name:'Shackleton Rim',lat:-89.10,lon:33.40,score:91,solar:88,earth:94,slope:4.8, demFile: 'shackleton_rim.tif'},
 {name:'Peak Near Shackleton',lat:-89.60,lon:145.00,score:78,solar:76,earth:82,slope:9.1, demFile: 'peak_near_shackleton.tif'},
 {name:'de Gerlache Rim',lat:-88.50,lon:-87.20,score:85,solar:86,earth:88,slope:7.1, demFile: 'de_gerlache_rim.tif'},
 {name:'Leibnitz Beta Plateau',lat:-85.20,lon:36.00,score:80,solar:84,earth:78,slope:8.3, demFile: 'leibnitz_beta.tif'},
 {name:'Malapert Massif',lat:-85.99,lon:0.45,score:87,solar:91,earth:83,slope:6.2, demFile: 'malapert_massif.tif'}
];
let selected=0, scene,camera,renderer,controls,moon,earth,sunLight,orbitLine,siteGroup,terrainGroup,earthLine,sunLine,stars,auto=true,clockT=0;
const toast=m=>{const t=$('toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2600)};

function makeMoonTexture() {
    const loader = new THREE.TextureLoader();
    const tex = loader.load('lroc_color_2k.jpg');
    tex.colorSpace = THREE.SRGBColorSpace;
    return tex;
}

// 3D viewport, camera, WebGL renderer, and lighting setup
function init3D(){
    const root=$('three-root');
    
    // Scene and exponential fog
    scene=new THREE.Scene();
    scene.fog=new THREE.FogExp2(0x030811,.018);

    // Perspective camera
    camera=new THREE.PerspectiveCamera(42,root.clientWidth/root.clientHeight,.1,2000);
    camera.position.set(0,2.2,7.4);renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});
    
    // WebGL renderer and ACES tone mapping
    renderer.setPixelRatio(Math.min(devicePixelRatio,2));
    renderer.setSize(root.clientWidth,root.clientHeight);
    renderer.outputColorSpace=THREE.SRGBColorSpace;
    renderer.toneMapping=THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure=1.18;root.appendChild(renderer.domElement);
    
    // Orbit controls
    controls=new OrbitControls(camera,renderer.domElement);
    controls.enableDamping=true;
    controls.dampingFactor=.045;
    controls.minDistance=2.6;
    controls.maxDistance=13;
    controls.autoRotate=true;
    controls.autoRotateSpeed=.35;

    // Three-point lighting (ambient, primary sunlight, and cool rim light)
    scene.add(new THREE.AmbientLight(0x9db9d2,.48));
    
    sunLight=new THREE.DirectionalLight(0xffe2bd,3.1);
    sunLight.position.set(-7,4,5);
    scene.add(sunLight);

    const rim=new THREE.PointLight(0x3e9dff,35,18);
    rim.position.set(4,1,-4);
    scene.add(rim);

const geo = new THREE.SphereGeometry(2, 160, 120);
const moonBumpTex = new THREE.TextureLoader().load('ldem_3_8bit.jpg');

const mat = new THREE.MeshStandardMaterial({
    map: makeMoonTexture(),
    bumpMap: moonBumpTex,
    bumpScale: 0.04,
    roughness: 1,
    metalness: 0
});
moon = new THREE.Mesh(geo, mat);
scene.add(moon);

terrainGroup = new THREE.Group();
moon.add(terrainGroup);

// South-Pole Locator Cap & Candidate Landing Beacons
siteGroup=new THREE.Group();
moon.add(siteGroup);

sites.forEach((site, index)=>{
    const phi = ((90 + site.lat) * Math.PI) / 180;
    const theta = ((site.lon + 180) * Math.PI) / 180;
    const radius = 2.018;
    
    const pos=new THREE.Vector3(
        2.018*Math.sin(phi)*Math.cos(theta),
        2.018*Math.cos(phi),
        2.018*Math.sin(phi)*Math.sin(theta)
    );
    
    const color=index===0?0x4ce4ff:0xffb45f;

    const pin=new THREE.Group();
    pin.position.copy(pos);
    pin.quaternion.setFromUnitVectors(
        new THREE.Vector3(0,1,0),
        pos.clone().normalize()
    );

    // Create center indicator dot
    const dotGeometry = new THREE.SphereGeometry(0.026, 16, 16);
    const dotMaterial = new THREE.MeshBasicMaterial({ color });
    const dot = new THREE.Mesh(dotGeometry, dotMaterial);
    pin.add(dot);

    // Create outer orbital halo ring
    const haloGeometry = new THREE.TorusGeometry(0.055, 0.004, 8, 40);
    const haloMaterial = new THREE.MeshBasicMaterial({
        color,
        transparent: true,
        opacity: 0.9,
    });
    const halo = new THREE.Mesh(haloGeometry, haloMaterial);
    halo.rotation.x = Math.PI / 2;
    pin.add(halo);

    // Store site index metadata and attach to scene group
    pin.userData.index = index;
    siteGroup.add(pin);
});

// Earth mesh and atmospheric glow sprite
earth=new THREE.Mesh(
    new THREE.SphereGeometry(.34,48,48),
    new THREE.MeshStandardMaterial({
        color:0x397dbb,
        roughness:.8,
        emissive:0x071d38,
        emissiveIntensity:.7,
    })
);
earth.position.set(4.5,1.7,-3.8);
scene.add(earth);

const earthGlow=new THREE.Sprite(
    new THREE.SpriteMaterial({
        color:0x398dff,
        transparent:true,
        opacity:.12,
    })
);
earthGlow.scale.set(1.4,1.4,1);
earth.add(earthGlow);

// Inclined lunar orbit trajectory line
const orbitPts=[];
for(let i=0;i<=200;i++){
    let a=i/200*Math.PI*2;
    orbitPts.push(
        new THREE.Vector3(
            Math.cos(a)*3.05,
            Math.sin(a)*.48,
            Math.sin(a)*3.05
        )
    );
}

orbitLine=new THREE.Line(
    new THREE.BufferGeometry().setFromPoints(orbitPts),
    new THREE.LineDashedMaterial({
        color:0x4a9bd9,
        dashSize:.06,
        gapSize:.045,
        transparent:true,
        opacity:.45
    })
);
orbitLine.computeLineDistances();
scene.add(orbitLine);

// Earth and sun trajectory lines
earthLine=new THREE.Line(
    new THREE.BufferGeometry(),
    new THREE.LineBasicMaterial({
        color:0x55e6c4,
        transparent:true,
        opacity:.75,
    })
);scene.add(earthLine);

sunLine=new THREE.Line(
    new THREE.BufferGeometry(),
    new THREE.LineBasicMaterial({
        color:0xffbd70,
        transparent:true,
        opacity:.7,
    })
);scene.add(sunLine);

// Background starfield particle system
const arr = [];

for (let i = 0; i < 1800; i++) {
  const v = new THREE.Vector3(
    (Math.random() - 0.5) * 90,
    (Math.random() - 0.5) * 55,
    (Math.random() - 0.5) * 90
  );

  if (v.length() < 15) {
    v.multiplyScalar(2);
  }

  arr.push(v.x, v.y, v.z);
}

const sg = new THREE.BufferGeometry();
sg.setAttribute('position', new THREE.Float32BufferAttribute(arr, 3));

stars = new THREE.Points(
  sg,
  new THREE.PointsMaterial({
    color: 0xa8d6f4,
    size: 0.035,
    transparent: true,
    opacity: 0.8,
  })
);

scene.add(stars);

// Viewport resize, interaction, and render loop
const resize = () => {
  const w = root.clientWidth;
  const h = root.clientHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
};

new ResizeObserver(resize).observe(root);

renderer.domElement.addEventListener('pointerdown', () => {
  controls.autoRotate = false;
});

animate();
}

// Main animation loop and celestial motion
function animate(){
    requestAnimationFrame(animate);
    
    // Advance simulation clock
    clockT+=.005;

    // Moon rotation
    if(auto)moon.rotation.y+=.0007;
    
    // Earth orbital drift and axial rotation
    earth.position.x=4.5+Math.sin(clockT*.35)*.25;
    earth.position.y=1.7+Math.cos(clockT*.35)*.12;
    earth.rotation.y+=.001;
    
    // Starfield parallax drift
    stars.rotation.y-=.00004;
    
    // Camera controls and scene rendering
    controls.update();
    renderer.render(scene,camera)
}

// Site-to-Earth & Sun line-of-sight (LOS) ray updaters
function updateLines(){
    const s=sites[selected];

    // Convert lunar lat/lon to 3D spherical coordinates (radius = 2.03)
    const phi=(90+s.lat)*Math.PI/180,theta=(s.lon+180)*Math.PI/180;
    const p=new THREE.Vector3(
        2.03*Math.sin(phi)*Math.cos(theta),
        2.03*Math.cos(phi),
        2.03*Math.sin(phi)*Math.sin(theta)
    );

    // Update Earth communication line
    const e=earth.position.clone();
    earthLine.geometry.dispose();
    earthLine.geometry=new THREE.BufferGeometry().setFromPoints([p,e]);

    // Update Sun illumination vector line
    const sun=new THREE.Vector3(-7,4,5).normalize().multiplyScalar(8);
    sunLine.geometry.dispose();
    sunLine.geometry=new THREE.BufferGeometry().setFromPoints([p,sun]);
}

// Candidate site beacons & selection list
function renderCandidates(){
    const box=$('candidateList');
    box.innerHTML='';

    sites.forEach((s,i)=>{
        const el=document.createElement('div');
        el.className='candidate '+(i===selected?'active':'');
        el.innerHTML=`
            <span class="rank">0${i + 1}</span>
            <div>
                <strong>${s.name}</strong>
                <small>${s.lat.toFixed(2)}° / ${s.lon.toFixed(2)}°</small>
            </div>
            <span class="candidate-score">${s.score}</span>
        `;
        
        el.onclick=()=>selectSite(i);
        box.appendChild(el);
    });
}

// Telemetry & Celestial Elevation Updater
function updateTelemetry() {
    const s = sites[selected];
    const minutes = +$('timeSlider').value; // Get current slider value in minutes (0 ~ 1440)
    const phase = (minutes / 1440) * Math.PI * 2; // Convert to 24-hour cycle radians

    // Dynamically compute solar elevation, Earth elevation, and illumination rate based on phase and site baseline
    const baseSolar = 4 + (selected * 1.37) % 6;
    const baseEarth = 2 + (selected * 2.1) % 7;

    const currentSolarElev = Math.max(0, baseSolar + Math.sin(phase - 1.2) * 3.2);
    const currentEarthElev = Math.max(0, baseEarth + Math.cos(phase - 0.5) * 2.8);
    const currentIllum = Math.min(100, Math.max(0, Math.round(s.solar + Math.sin(phase - 1.2) * 18)));

    // Update the three telemetry metric cards in the UI
    $('solarElev').innerHTML = currentSolarElev.toFixed(2) + '<span>°</span>';
    $('earthElev').innerHTML = currentEarthElev.toFixed(2) + '<span>°</span>';
    $('illumination').innerHTML = currentIllum + '.<span>%</span>';
}

function selectSite(i){
    selected=i;
    const s=sites[i];
    $('siteSelect').value=s.name;
    $('lat').textContent=s.lat.toFixed(2)+'°';
    $('lon').textContent=(s.lon>0?'+':'')+s.lon.toFixed(2)+'°';
    $('calloutName').textContent=s.name.toUpperCase();
    $('score').textContent=s.score;
    $('illumination').innerHTML=s.solar+'.<span>%</span>';
    $('commWindow').innerHTML=s.earth+'.<span>%</span>';
    $('slope').innerHTML=s.slope+'.<span>°</span>';
    $('solarElev').innerHTML=(4+(i*1.37)%6).toFixed(2)+'<span>°</span>';
    $('earthElev').innerHTML=(2+(i*2.1)%7).toFixed(2)+'<span>°</span>';
    
    updateTelemetry();
    renderCandidates();
    updateLines()

    // Sync local 3D DEM terrain on site change only when TERRAIN LAB is active
    if (currentView === 'terrain') {
        loadRealDemTerrain(s.demFile);
    }
}

// 24 hour illumination & visibility timeline chart
function drawTimeline(){
    const c = $('timelineChart');
    const ctx = c.getContext('2d');
    const w = c.clientWidth;
    const h = 125;
    const dpr = devicePixelRatio || 1;
    
    // Handle high-DPI scaling and clear canvas
    c.width=w*dpr;
    c.height=h*dpr;
    ctx.scale(dpr,dpr);
    ctx.clearRect(0,0,w,h);
    
    // Define chart padding and inner dimensions
    const pad={l:25,r:8,t:12,b:20};
    const cw=w-pad.l-pad.r;
    const ch=h-pad.t-pad.b;
    
    // Draw horizontal grid lines and Y-axis percentage labels
    ctx.strokeStyle='#1a3448';
    ctx.lineWidth=1;
    for(let i=0;i<4;i++){
        let y=pad.t+ch*i/3;
        ctx.beginPath();
        ctx.moveTo(pad.l,y);
        ctx.lineTo(w-pad.r,y);
        ctx.stroke();
        ctx.fillStyle='#66859a';
        ctx.font='8px IBM Plex Mono';
        ctx.fillText((100-i*33)+'%',1,y+3)
    }

    // Helper function to plot smooth glowing data curves
    const draw=(color,fn)=>{
        ctx.beginPath();
        for(let i=0;i<=120;i++){
            const x=i/120*24;
            const val=fn(x);
            const y=pad.t+ch*(1-val);
            
            if(i===0)ctx.moveTo(pad.l+x/24*cw,y);
            else ctx.lineTo(pad.l+x/24*cw,y)
        }
        ctx.strokeStyle=color;
        ctx.lineWidth=1.8;
        ctx.shadowColor=color;
        ctx.shadowBlur=7;
        ctx.stroke();
        ctx.shadowBlur=0
    };

    const hour=+$('timeSlider').value/60;

    // Render illumination (amber) and Earth-link visibility (cyan) curves
    draw('#ffb45f', x => Math.max(0, Math.sin((x + hour - 5) / 24 * Math.PI * 2) * .42 + .52));
    draw('#51d8ff', x => Math.max(0, Math.sin((x + hour + 1) / 24 * Math.PI * 2) * .28 + .65));
        
    ctx.fillStyle='#67879d';
    ctx.font='8px IBM Plex Mono';
    ['00','06','12','18','24'].forEach((v,i)=>ctx.fillText(v+':00',pad.l+i*cw/4-8,h-3));
        
    // Draw vertical dashed indicator for current slider time
    let x=pad.l+hour/24*cw;
    ctx.strokeStyle='#dff8ff88';
    ctx.setLineDash([3,3]);
    ctx.beginPath();
    ctx.moveTo(x,pad.t);
    ctx.lineTo(x,pad.t+ch);
    ctx.stroke();
    ctx.setLineDash([])
}

function setView(v) {
    currentView = v;
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.toggle('active', b.dataset.view === v));

    if (v === 'terrain') {
        controls.autoRotate = false;
        camera.position.set(0, 2.2, 3.8);

        // Hide the full Moon, Earth, and orbital lines;
        moon.visible = false;
        earth.visible = false;
        orbitLine.visible = false;
        earthLine.visible = false;
        sunLine.visible = false;

        // Load real-world DEM terrain
        const currentSite = sites[selected];
        loadRealDemTerrain(currentSite.demFile);
        fetchRealDemFromCatalog();
        toast('TERRAIN LAB · Loading into real 3D DEM terrain...');
    } else if (v === 'optimization') {
        camera.position.set(4, 3, 6);
        moon.visible = true;
        earth.visible = true;
        orbitLine.visible = true;
        earthLine.visible = true;
        sunLine.visible = true;
        if (window.activeDemMesh) window.activeDemMesh.visible = false;
        toast('OPTIMIZATION LAB · Run Pareto analysis from mission panel');
    } else {
        camera.position.set(0, 2.2, 7.4);
        controls.autoRotate = auto;
        moon.visible = true;
        earth.visible = true;
        orbitLine.visible = true;
        earthLine.visible = true;
        sunLine.visible = true;
        if (window.activeDemMesh) window.activeDemMesh.visible = false;
        toast('MISSION CONTROL ACTIVE');
    }
    controls.target.set(0, 0, 0);
}

const DEM_API_BASE = "http://127.0.0.1:8000";

async function fetchRealDemFromCatalog() {
    try {
        const res = await fetch(`${DEM_API_BASE}/api/dem/catalog`);
        const catalog = await res.json();
        const files = Array.isArray(catalog) ? catalog : (catalog.files || catalog.items || []);
        if (files.length === 0) {
            toast('There are currently no .tif files in the data folder');
            return;
        }
        const firstFile = typeof files[0] === 'string' ? files[0] : files[0].filename;
        await loadRealDemTerrain(firstFile);
    } catch (err) {
        console.error('Failed to query the DEM directory:', err);
    }
}

async function loadRealDemTerrain(filename) {
    try {
        const res = await fetch(`${DEM_API_BASE}/api/dem/heightmap?filename=${encodeURIComponent(filename)}&size=128`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const { width, height, grid } = await res.json();

        const geometry = new THREE.PlaneGeometry(3.2, 3.2, width - 1, height - 1);
        const vertices = geometry.attributes.position.array;
        const heightScale = 0.55;

        for (let r = 0; r < height; r++) {
            for (let c = 0; c < width; c++) {
                const idx = (r * width + c) * 3;
                vertices[idx + 2] = grid[r][c] * heightScale;
            }
        }

        geometry.attributes.position.needsUpdate = true;
        geometry.computeVertexNormals();

        const material = new THREE.MeshStandardMaterial({
            color: 0xa39f96,
            roughness: 0.9,
            metalness: 0.05
        });

        if (window.activeDemMesh) scene.remove(window.activeDemMesh);

        const demMesh = new THREE.Mesh(geometry, material);
        demMesh.rotation.x = -Math.PI / 2;
        demMesh.castShadow = true;
        demMesh.receiveShadow = true;

        window.activeDemMesh = demMesh;
        scene.add(demMesh);
        toast(`TERRAIN LAB · LOADED ${filename}`);
    } catch (err) {
        console.error('Failed to load 3D DEM:', err);
    }
}

async function checkAPI(){
    try{const r=await fetch(API+'/api/health',{signal:AbortSignal.timeout(1800)});
    if(!r.ok)throw Error();
    const j=await r.json();
    $('apiState').textContent='CONNECTED';
    $('apiState').style.color='#6be0b0';
    return true}catch{$('apiState').textContent='OFFLINE / DEMO';return false}
}

// Backend API check and NSGA-II Pareto site optimization
async function runPareto(){
    const ok=await checkAPI();
    if(!ok){
        toast('Backend offline. Start FastAPI to run real NSGA-II optimization.');
        return;
    }
    const candidates=sites.map((s,i)=>({
        id:`SITE-${String(i+1).padStart(2,'0')}`,
        name:s.name,
        sunlight_pct:s.solar,
        communication_pct:s.earth,
        slope_deg:s.slope
    }));
    
    try{
        const r=await fetch(API+'/api/optimization/pareto',{
            method:'POST',
            headers:{
                'Content-Type':'application/json'
            },
            body:JSON.stringify({
                candidates,
                population_size:80,
                generations:80,
                seed:17
            })
        });
        
        if(!r.ok)throw Error(await r.text());
        
        const data=await r.json();
        const count = (data.pareto_front || []).length;
        toast(`PARETO COMPLETE · ${count} NON-DOMINATED SOLUTIONS`);
    }   catch (e) {
        toast(`Optimization API error: ${e.message}`);
    }
}

// UI event bindings and 3D viewport controls
function bind(){
    // Landing site selection & timeline scrubber
    $('siteSelect').onchange=e=>selectSite(sites.findIndex(s=>s.name===e.target.value));
    $('timeSlider').oninput=e=>{
        let n=+e.target.value,h=Math.floor(n/60),m=n%60;
        $('timeValue').textContent=String(h).padStart(2,'0')+':'+String(m).padStart(2,'0')+':00';
        updateTelemetry();
        drawTimeline();
    };

    // 3D scene layer visibility toggles
    $('terrainToggle').onchange=e=>terrainGroup.visible=e.target.checked;
    $('orbitToggle').onchange=e=>orbitLine.visible=e.target.checked;
    $('sunToggle').onchange=e=>sunLine.visible=e.target.checked;
    $('earthToggle').onchange=e=>earthLine.visible=e.target.checked;
    
    // Camera & viewport controls
    $('autoRotate').onclick=()=>{
        auto=!auto;
        controls.autoRotate=auto;
        $('autoRotate').classList.toggle('selected',auto)
    };

    $('resetCamera').onclick=()=>{
        camera.position.set(0,2.2,7.4);
        controls.target.set(0,0,0);
        controls.autoRotate=auto
    };

    $('zoomIn').onclick=()=>camera.position.multiplyScalar(.86);
    $('zoomOut').onclick=()=>camera.position.multiplyScalar(1.16);
    $('fullscreen').onclick=()=>document.documentElement.requestFullscreen?.();
    
    // Pareto optimization trigger & view navigation
    $('runOptimization').onclick=runPareto;
    document.querySelectorAll('.nav-btn').forEach(b => {
        b.onclick = () => setView(b.dataset.view);
    });
    window.addEventListener('resize',drawTimeline)
}

async function start(){
    init3D();
    renderCandidates();
    selectSite(0);
    bind();
    drawTimeline();
    await checkAPI();
    setInterval(()=>{
        $('clock').textContent=new Date().toISOString().slice(11,19)+' UTC'},1000);
        setTimeout(()=>{$('boot').style.display='none';
            $('app').classList.remove('hidden')},900)}start().catch(e=>{console.error(e);
        $('boot').innerHTML='<b>3D ENGINE INITIALIZATION FAILED</b><p>Use a modern browser with WebGL enabled and internet access for Three.js CDN.</p>'}
);