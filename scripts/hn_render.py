"""Blender 4.5 Eevee. Metric GSI DEM (x2 vertical exaggeration, disclosed), GSI aerial texture, symbolic markers."""
import bpy,sys,json,math,time
import numpy as np
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:]
mode=args[0];r0=int(args[1]) if len(args)>1 and mode!='test' else 0;r1=int(args[2]) if len(args)>2 and mode!='test' else 10**9
VZ=2.0
import os
META=os.environ.get('HN_META')=='1'
out=ROOT/'cache'/(os.environ.get('HN_OUT') or ('hn_v3' if mode in ('test','main') else f'hn_{mode}'));out.mkdir(parents=True,exist_ok=True)
g=np.load(ROOT/'data'/'hn_terrain.npz');xs,ys,h=g['xs'],g['ys'],g['h'];step=float(xs[1]-xs[0])
def height(x,y):
    u=(x-xs[0])/step;v=(y-ys[0])/step;i=min(max(int(u),0),len(xs)-2);j=min(max(int(v),0),len(ys)-2);a=u-i;b=v-j
    if a+b<=1:z=h[j,i]*(1-a-b)+h[j,i+1]*a+h[j+1,i]*b
    else:z=h[j+1,i+1]*(a+b-1)+h[j,i+1]*(1-b)+h[j+1,i]*(1-a)
    return float(z)*VZ
places=json.loads((ROOT/'data'/'hn_places.json').read_text(encoding='utf8'));ana=json.loads((ROOT/'data'/'hn_analysis.json').read_text(encoding='utf8'))
route=np.array(ana['route_xy'])[:,:2];seg=np.hypot(*np.diff(route,axis=0).T);cum=np.concatenate([[0],np.cumsum(seg)]);total=cum[-1]
def on_route(p):
    d=min(max(p,0),1)*total;x=np.interp(d,cum,route[:,0]);y=np.interp(d,cum,route[:,1]);return float(x),float(y)
timeline=json.loads((ROOT/'data'/'hn_timeline.json').read_text(encoding='utf8'));cams=json.loads((ROOT/'data'/'hn_cameras.json').read_text(encoding='utf8'))
is3d=lambda i:cams[timeline[i]['key']].get('kind') not in ('map','trivia')
N=round(timeline[-1]['end']*30)
HOOK_SKIP=float(json.loads((ROOT/'data'/'hn_timeline.json').read_text(encoding='utf8'))[0].get('hook_end',0))-1.0
if mode=='bench':fr_list=[round((timeline[i]['start']+timeline[i]['duration']*.5)*30) for i in range(len(timeline)) if is3d(i)]
elif mode=='test':fr_list=[int(x) for x in args[1].split(',')]
else:fr_list=[f for f in range(r0,min(N,r1)) if (not os.environ.get('HN_KEYS') or timeline[next(i for i,c in enumerate(timeline) if f/30<c['end']+1e-9)]['key'] in os.environ['HN_KEYS'].split(',')) and is3d(next(i for i,c in enumerate(timeline) if f/30<c['end']+1e-9)) and not (f/30<HOOK_SKIP) and (META or not (out/f'{f:05}.jpg').exists())]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=24
s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=50 if mode=='bench' else 100
s.render.image_settings.file_format='JPEG';s.render.image_settings.quality=95;s.render.fps=30
s.view_settings.view_transform='AgX'
if s.world is None:s.world=bpy.data.worlds.new('w')
w=s.world;w.use_nodes=True;bg=w.node_tree.nodes['Background'];bg.inputs['Strength'].default_value=1.0
def mat(name,color,rough=.8,emission=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
    if emission:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
    return m
tm=bpy.data.materials.new('terrain');tm.use_nodes=True;nt=tm.node_tree;p=nt.nodes['Principled BSDF'];p.inputs['Roughness'].default_value=1
tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'cache'/'hn_texture.png'));tex.image.colorspace_settings.name='sRGB';nt.links.new(tex.outputs['Color'],p.inputs['Base Color'])
nx,ny=len(xs),len(ys);verts=[(float(x),float(y),float(h[j,i])*VZ) for j,y in enumerate(ys) for i,x in enumerate(xs)];faces=[]
for j in range(ny-1):
    for i in range(nx-1):
        a=j*nx+i;faces.extend([(a,a+1,a+nx),(a+1,a+nx+1,a+nx)])
me=bpy.data.meshes.new('DEM');me.from_pydata(verts,[],faces);me.update()
uv=me.uv_layers.new(name='uv')
for poly in me.polygons:
    for li in poly.loop_indices:
        v=verts[me.loops[li].vertex_index];uv.data[li].uv=((v[0]-xs[0])/(xs[-1]-xs[0]),(v[1]-ys[0])/(ys[-1]-ys[0]))
for poly in me.polygons:poly.use_smooth=True
ob=bpy.data.objects.new('DEM_x2',me);s.collection.objects.link(ob);ob.data.materials.append(tm)

# --- high-res central patch (GSI ort z17, feathered alpha); coplanar with the DEM triangulation, lifted 1.2 m
pj=json.loads((ROOT/'data'/'hn_patch.json').read_text());pxa,pxb,pya,pyb=pj['extent_m'];S=10.0
pxs=np.arange(math.ceil(pxa/S)*S,pxb,S);pys=np.arange(math.ceil(pya/S)*S,pyb,S);pnx=len(pxs)
pv=[(float(x),float(y),height(float(x),float(y))+1.2) for y in pys for x in pxs];pf=[]
for j in range(len(pys)-1):
    for i in range(pnx-1):
        a=j*pnx+i;pf.append((a,a+1,a+pnx));pf.append((a+1,a+pnx+1,a+pnx))
pm=bpy.data.meshes.new('patch');pm.from_pydata(pv,[],pf);pm.update();puv=pm.uv_layers.new(name='uv')
for poly in pm.polygons:
    for li in poly.loop_indices:
        v=pv[pm.loops[li].vertex_index];puv.data[li].uv=((v[0]-pxa)/(pxb-pxa),(v[1]-pya)/(pyb-pya))
for poly in pm.polygons:poly.use_smooth=True
patm=bpy.data.materials.new('patch');patm.use_nodes=True;pnt=patm.node_tree;pp_=pnt.nodes['Principled BSDF'];pp_.inputs['Roughness'].default_value=1
ptex=pnt.nodes.new('ShaderNodeTexImage');ptex.image=bpy.data.images.load(str(ROOT/'cache'/'hn_patch.png'));ptex.image.colorspace_settings.name='sRGB';ptex.image.alpha_mode='STRAIGHT'
pnt.links.new(ptex.outputs['Color'],pp_.inputs['Base Color']);pnt.links.new(ptex.outputs['Alpha'],pp_.inputs['Alpha'])
po=bpy.data.objects.new('patch',pm);s.collection.objects.link(po);po.data.materials.append(patm)
edge=list(range(nx))+[j*nx+nx-1 for j in range(1,ny)]+list(range((ny-1)*nx+nx-2,(ny-1)*nx-1,-1))+[j*nx for j in range(ny-2,0,-1)]
sv=[];sf=[]
for idx in edge:
    x,y,z=verts[idx];sv.extend([(x,y,z),(x,y,-60)])
for k in range(len(edge)):
    a=2*k;b=2*((k+1)%len(edge));sf.append((a,b,b+1,a+1))
m2=bpy.data.meshes.new('skirt');m2.from_pydata(sv,[],sf);o2=bpy.data.objects.new('skirt',m2);s.collection.objects.link(o2);o2.data.materials.append(mat('skirt',(.06,.07,.08)))
purple=mat('akechi',(.30,.05,.9),emission=.25);red=mat('oda',(.9,.03,.01),emission=.3);gold=mat('place',(1,.55,.02),emission=.3);white=mat('now',(.55,.7,1),emission=.25);pole_m=mat('pole',(.05,.05,.06))
cols={'kameyama':purple,'honnoji':red,'honnoji_now':white,'nijo':red,'oinosaka':gold}
def cube(name,loc,dim,m):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);return o
markers={}
for k,pl in places.items():
    x,y=pl['x_m'],pl['y_m'];pole=cube(k+'_pole',(x,y,0),(1,1,1),pole_m);flag=cube(k+'_flag',(x,y,0),(1,1,1),cols[k])
    markers[k]=(pole,flag,x,y)
cu=bpy.data.curves.new('route','CURVE');cu.dimensions='3D';cu.bevel_depth=14;sp=cu.splines.new('POLY');pts=[(x,y,height(x,y)+6) for x,y in route[::2]];sp.points.add(len(pts)-1)
for pp,v in zip(sp.points,pts):pp.co=(*v,1)
route_o=bpy.data.objects.new('route',cu);s.collection.objects.link(route_o);route_o.data.materials.append(mat('route',(1,.6,.05),emission=.5))
def sprite_mats(prefix,files,emission=0.0,glow=False):
    ms=[]
    for k,f in enumerate(files):
        m=bpy.data.materials.new(f'{prefix}{k}');m.use_nodes=True;n=m.node_tree;p_=n.nodes['Principled BSDF'];p_.inputs['Roughness'].default_value=1
        im=bpy.data.images.load(str(f));im.alpha_mode='STRAIGHT';ti=n.nodes.new('ShaderNodeTexImage');ti.image=im;ti.interpolation='Linear'
        if glow:
            p_.inputs['Base Color'].default_value=(0,0,0,1);n.links.new(ti.outputs['Color'],p_.inputs['Emission Color']);p_.inputs['Emission Strength'].default_value=emission
        else:
            n.links.new(ti.outputs['Color'],p_.inputs['Base Color']);n.links.new(ti.outputs['Color'],p_.inputs['Emission Color']);p_.inputs['Emission Strength'].default_value=emission
        fade=n.nodes.new('ShaderNodeValue');fade.name='fade';fade.outputs[0].default_value=1.0;mul=n.nodes.new('ShaderNodeMath');mul.operation='MULTIPLY'
        n.links.new(ti.outputs['Alpha'],mul.inputs[0]);n.links.new(fade.outputs[0],mul.inputs[1]);n.links.new(mul.outputs[0],p_.inputs['Alpha']);m.use_backface_culling=False;ms.append(m)
    return ms
def billboard(name,m):
    me_=bpy.data.meshes.new(name);me_.from_pydata([(-.5,0,0),(.5,0,0),(.5,1,0),(-.5,1,0)],[],[(0,1,2,3)]);me_.update();u_=me_.uv_layers.new(name='uv')
    for li,uv_ in zip(range(4),[(0,0),(1,0),(1,1),(0,1)]):u_.data[li].uv=uv_
    o=bpy.data.objects.new(name,me_);s.collection.objects.link(o);o.data.materials.append(m);o.visible_shadow=False;return o
AK=sprite_mats('ak',[ROOT/'assets'/'army_hn'/f'akechi_{i:02}.png' for i in range(12)],emission=.7);OD=sprite_mats('od',[ROOT/'assets'/'army_hn'/f'oda_{i:02}.png' for i in range(12)],emission=.7)
FL=sprite_mats('fl',[ROOT/'assets'/'fx_hn'/f'flame_{i}.png' for i in range(4)],emission=3.0,glow=True)
SM=sprite_mats('sm',[ROOT/'assets'/'fx_hn'/'smoke.png' for i in range(8)])
NA=14;army=[billboard(f'army{i}',AK[0]) for i in range(NA)]
ring=[billboard(f'siege{i}',AK[0]) for i in range(12)];guards=[billboard(f'guard{i}',OD[0]) for i in range(4)]
fire=[billboard(f'fire{i}',FL[i%4]) for i in range(8)];smoke=[billboard(f'smoke{i}',SM[i]) for i in range(8)]
bpy.ops.curve.primitive_bezier_curve_add();bpy.data.objects.remove(bpy.context.object)
oc=bpy.data.curves.new('compound','CURVE');oc.dimensions='3D';oc.bevel_depth=1.6;osp=oc.splines.new('POLY');osp.points.add(4);osp.use_cyclic_u=True
compound=bpy.data.objects.new('compound',oc);s.collection.objects.link(compound);compound.data.materials.append(mat('compound',(1,.12,.05),emission=1.2))
bpy.ops.mesh.primitive_cone_add(vertices=3,radius1=1,depth=2);arrow=bpy.context.object;arrow.data.materials.append(gold);arrow.name='south_arrow'
shaft=cube('south_shaft',(0,0,0),(1,1,1),gold)
bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.data.angle=.04
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.lens=35;cam.data.clip_start=20;cam.data.clip_end=90000
cx=(xs[0]+xs[-1])/2;cy=(ys[0]+ys[-1])/2
def lerp(a,b,t):return a+(b-a)*t
def ease(t):return t*t*(3-2*t)
metrics=[];contact=[];t0=time.time()
for frame in fr_list:
    tsec=frame/30;ci=next(i for i,c in enumerate(timeline) if tsec<c['end']+1e-9);ch=timeline[ci];sc=cams[ch['key']];local=min(1,max(0,(tsec-ch['start'])/ch['duration']));e=ease(local)
    ap=lerp(sc['army'][0],sc['army'][1],local)
    hx,hy=on_route(ap)
    tg=sc['target']
    if tg=='center':X,Y=cx,cy
    elif tg=='army':fp=lerp(sc['follow'][0],sc['follow'][1],local);X,Y=on_route(fp)
    elif tg=='route_mid':X,Y=on_route(.5)
    elif tg=='mid_honnoji':X=(places['honnoji']['x_m']+places['honnoji_now']['x_m'])/2;Y=(places['honnoji']['y_m']+places['honnoji_now']['y_m'])/2
    elif tg=='mid_nijo':X=(places['honnoji']['x_m']+places['nijo']['x_m'])/2;Y=(places['honnoji']['y_m']+places['nijo']['y_m'])/2
    elif tg=='honnoji_south':X,Y=places['honnoji']['x_m'],places['honnoji']['y_m']-2500
    else:X,Y=places[tg]['x_m'],places[tg]['y_m']
    Z=height(X,Y);az=math.radians(lerp(sc['az'][0],sc['az'][1],e));el=math.radians(sc['elev']);d=sc['dist']
    camloc=Vector((X+d*math.cos(el)*math.sin(az),Y-d*math.cos(el)*math.cos(az),Z+d*math.sin(el)));cam.location=camloc
    cam.rotation_euler=(Vector((X,Y,Z))-camloc).to_track_quat('-Z','Y').to_euler()
    k_=d/5500
    for k,(pole,flag,x,y) in markers.items():
        vis=k in sc['marks'];z=height(x,y)
        for o in (pole,flag):o.hide_render=not vis
        if vis:
            H=520*k_;pole.dimensions=(14*k_,14*k_,H);pole.location=(x,y,z+H/2);flag.dimensions=(200*k_,10*k_,110*k_);flag.location=(x+110*k_,y,z+H-70*k_)
    show_army=bool(sc.get('army_on'))
    route_o.hide_render=not show_army
    SPW=300*k_;SPAC=max(.0075,SPW*1.05/total)
    cam_rot=cam.rotation_euler.copy()
    def place(o,px,py,w,mats,idx,lift=0):
        o.location=(px,py,height(px,py)+lift);o.rotation_euler=cam_rot;o.scale=(w,w/1.25,1);o.data.materials[0]=mats[idx%len(mats)]
    for i,o in enumerate(army):
        pi_=ap-i*SPAC;vis=show_army and 0<=pi_<=1.0001 and not (ci in (2,) and False)
        o.hide_render=not vis
        if vis:
            px,py=on_route(pi_);place(o,px,py,SPW,AK,(frame//2+i*3)%12,-SPW*.02);contact.append(0.0)
    bx,by=places['honnoji']['x_m'],places['honnoji']['y_m']
    siege=bool(sc.get('siege'));rr_=lerp(520,260,ease(min(1,local*2.0)))
    for i,o in enumerate(ring):
        o.hide_render=not siege
        if siege:
            a_=2*math.pi*i/len(ring)+.3;px,py=bx+rr_*math.cos(a_),by+rr_*math.sin(a_);place(o,px,py,100,AK,(frame//2+i*3)%12)
    for i,o in enumerate(guards):
        o.hide_render=not siege
        if siege:
            a_=2*math.pi*i/4+.8;px,py=bx+34*math.cos(a_),by+34*math.sin(a_);place(o,px,py,70,OD,(frame//3+i*5)%12)
    cpts=[(-60,-60),(60,-60),(60,60),(-60,60),(-60,-60)]
    show_c=bool(sc.get('compound'))
    compound.hide_render=not show_c
    if show_c:
        for pt,(dx,dy) in zip(osp.points,cpts):pt.co=(bx+dx,by+dy,height(bx+dx,by+dy)+3,1)
    fmode=sc.get('fire');fire_on=(fmode=='ignite' and local>.40) or fmode=='keep'
    fgrow=min(1,(local-.40)/.25) if fmode=='ignite' else 1.0
    for i,o in enumerate(fire):
        o.hide_render=not fire_on
        if fire_on:
            a_=i*2.4;rd=10+i*6.5;fx,fy=bx+rd*math.cos(a_),by+rd*math.sin(a_);fl=(1+.28*math.sin(tsec*11+i*1.9))*fgrow
            place(o,fx,fy,(62+i*5)*fl,FL,(frame//3+i)%4)
    for i,o in enumerate(smoke):
        o.hide_render=not fire_on
        if fire_on:
            life=((tsec*.11+i/8.0)%1.0);sz=(90+420*life)*fgrow;a_=i*1.3;sx=bx+30*math.cos(a_)+life*140;sy=by+30*math.sin(a_)+life*60;z0=height(sx,sy)
            o.location=(sx,sy,z0+60+life*620);o.rotation_euler=cam_rot;o.scale=(sz,sz/1.0,1)
            SM[i].node_tree.nodes['fade'].outputs[0].default_value=float(min(1,life*6)*(1-life)**1.2*.75*fgrow)
    arrow.hide_render=not sc.get('arrow_south');shaft.hide_render=arrow.hide_render
    if sc.get('arrow_south'):
        ax,ay=bx-200,by-2500+400*math.sin(tsec*2);arrow.location=(ax,ay,height(ax,ay)+700);arrow.rotation_euler=(math.radians(90),0,0);arrow.scale=(220,220,220);shaft.location=(ax,ay+520,height(ax,ay)+700);shaft.dimensions=(120,700,120)
    dawn=bool(sc.get('dawn'))
    sun.data.energy=2.2 if dawn else 4.0;sun.data.color=(1,.55,.35) if dawn else (1,.95,.85)
    sun.rotation_euler=(math.radians(78 if dawn else 62),0,math.radians(110 if dawn else -40))
    bg.inputs['Color'].default_value=(.01,.015,.03,1) if dawn else (.007,.014,.026,1)
    s.frame_set(frame+1);bpy.context.view_layer.update()
    labels=[]
    for k in sc['marks']:
        pole,flag,x,y=markers[k];v=world_to_camera_view(s,cam,Vector((x,y,height(x,y)+560*k_)));labels.append(dict(id=k,x=float(v.x),y=float(1-v.y),depth=float(v.z)))
    if show_army:
        v=world_to_camera_view(s,cam,Vector((hx,hy,height(hx,hy)+160*k_)));labels.append(dict(id='army',x=float(v.x),y=float(1-v.y),depth=float(v.z)))
    n=time.perf_counter();s.render.filepath=str(out/(f'{frame:05}.jpg' if mode!='bench' else f'bench_{ci:02}.jpg'));(None if META else bpy.ops.render.render(write_still=True))
    metrics.append(dict(frame=frame,scene=ci,render_seconds=time.perf_counter()-n,labels=labels,army_progress=ap,local=local))
    if frame%50==0:print('frame',frame,round(metrics[-1]['render_seconds'],2),flush=True)
(out/(f'report_{r0}_{r1}.json' if mode!='test' else 'report_test.json') if not META else out/f'report_meta_{r0}_{r1}.json').write_text(json.dumps(dict(frames=metrics,vertical_exaggeration=VZ,max_foot_contact_error_m=max(contact,default=0),total_s=time.time()-t0),indent=1),encoding='utf8')
