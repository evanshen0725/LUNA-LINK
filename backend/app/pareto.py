"""Small dependency-free NSGA-II implementation for landing-site candidates."""
import random

def dominates(a,b):
    return all(x <= y for x,y in zip(a,b)) and any(x < y for x,y in zip(a,b))

def fast_sort(pop):
    fronts=[[]]; counts=[0]*len(pop); beaten=[[] for _ in pop]
    for i,p in enumerate(pop):
        for j,q in enumerate(pop):
            if i==j: continue
            if dominates(p['objectives'],q['objectives']): beaten[i].append(j)
            elif dominates(q['objectives'],p['objectives']): counts[i]+=1
        if counts[i]==0: fronts[0].append(i)
    k=0
    while k<len(fronts) and fronts[k]:
        nxt=[]
        for i in fronts[k]:
            for j in beaten[i]:
                counts[j]-=1
                if counts[j]==0: nxt.append(j)
        if nxt: fronts.append(nxt)
        k+=1
    return [[pop[i] for i in f] for f in fronts if f]

def crowding(front):
    if not front: return
    for p in front: p['crowding']=0.0
    m=len(front[0]['objectives'])
    for k in range(m):
        s=sorted(front,key=lambda p:p['objectives'][k]); s[0]['crowding']=s[-1]['crowding']=float('inf')
        lo,hi=s[0]['objectives'][k],s[-1]['objectives'][k]
        if hi==lo: continue
        for i in range(1,len(s)-1): s[i]['crowding']+=(s[i+1]['objectives'][k]-s[i-1]['objectives'][k])/(hi-lo)

def optimize_sites(candidates, population_size=80, generations=80, seed=7):
    """Optimize candidate metrics; objectives are maximize sunlight, comms and
    minimize slope. Candidate inputs: id, sunlight_pct, communication_pct,
    slope_deg, optional x/y. Values are normalized internally to minimization.
    This is a discrete candidate-selection NSGA-II baseline, not a landing
    safety certification or a continuous geographic optimizer.
    """
    if len(candidates)<2: raise ValueError('At least two candidates are required')
    for c in candidates:
        for key in ('sunlight_pct','communication_pct','slope_deg'):
            if key not in c or not isinstance(c[key],(int,float)): raise ValueError(f'Missing numeric {key}')
        if not 0<=c['sunlight_pct']<=100 or not 0<=c['communication_pct']<=100 or c['slope_deg']<0:
            raise ValueError('Invalid candidate metrics')
    rng=random.Random(seed)
    pool=[dict(c,objectives=[-c['sunlight_pct']/100,-c['communication_pct']/100,c['slope_deg']/90]) for c in candidates]
    pop=[rng.choice(pool).copy() for _ in range(population_size)]
    for _ in range(generations):
        fronts=fast_sort(pop)
        for f in fronts: crowding(f)
        ranked=[p for f in fronts for p in sorted(f,key=lambda x:x.get('crowding',0),reverse=True)]
        # Discrete mutation/crossover: offspring remain actual evaluated sites.
        children=[]
        while len(children)<population_size:
            a,b=rng.choice(ranked[:max(2,population_size//2)]),rng.choice(ranked[:max(2,population_size//2)])
            child=(a if rng.random()<.5 else b).copy()
            if rng.random()<.35: child=rng.choice(pool).copy()
            children.append(child)
        combined=pop+children; new=[]
        for f in fast_sort(combined):
            crowding(f)
            f=sorted(f,key=lambda x:x.get('crowding',0),reverse=True)
            new.extend(f[:population_size-len(new)])
            if len(new)>=population_size: break
        pop=new
    front=fast_sort(pop)[0]
    unique={p['id']:p for p in front}
    results=[]
    for p in unique.values():
        results.append({k:v for k,v in p.items() if k!='objectives' and k!='crowding'})
    return {"algorithm":"NSGA-II (discrete candidate baseline)","generations":generations,
            "population_size":population_size,"objectives":["maximize sunlight_pct","maximize communication_pct","minimize slope_deg"],
            "pareto_front":results,"note":"Pareto set ranks only supplied candidate metrics. Ensure metrics are measured over the same interval, at a documented height, with consistent terrain/ephemeris frames."}
