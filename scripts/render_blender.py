"""Blender 4.5 Eevee renderer. Metric DEM, barycentric ground contact, linked symbols."""
import bpy,sys,json,math,time
import numpy as np
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:]
level=int(args[0]);mode=args[1] if len(args)>1 else 'bench'
out=ROOT/'cache'/f'render_l{level}_{mode}';out.mkdir(parents=True,exist_ok=True)
grid=np.load(ROOT/'data'/'terrain.npz');xs,ys,h=grid['xs'],grid['ys'],grid['h'];step=float(xs[1]-xs[0])
def height(x,y):
    u=(x-xs[0])/step;v=(y-ys[0])/step;i=int(u);j=int(v);a=u-i;b=v-j
    assert 0<=i<len(xs)-1 and 0<=j<len(ys)-1
    # triangles exactly match mesh triangulation
    if a+b<=1:return float(h[j,i]*(1-a-b)+h[j,i+1]*a+h[j+1,i]*b)
    return float(h[j+1,i+1]*(a+b-1)+h[j,i+1]*(1-b)+h[j+1,i]*(1-a))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=16 if level<3 else 32
s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=50 if mode=='bench' else 100
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.compression=15
if mode=='pilot':s.render.image_settings.file_format='JPEG';s.render.image_settings.quality=95
s.render.fps=30;s.world.color=(.18,.22,.27);s.view_settings.view_transform='AgX'
def mat(name,color,rough=1,emission=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
    if emission:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
    return m
terrainmat=mat('Procedural terrain - illustrative',(.24,.33,.21))
nodes=terrainmat.node_tree.nodes;links=terrainmat.node_tree.links;p=nodes.get('Principled BSDF')
noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=0.007;noise.inputs['Detail'].default_value=3
coord=nodes.new('ShaderNodeTexCoord');links.new(coord.outputs['Generated'],noise.inputs['Vector']);noise.inputs['Scale'].default_value=18
ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.22;ramp.color_ramp.elements[0].color=(.10,.18,.13,1);ramp.color_ramp.elements[1].position=.78;ramp.color_ramp.elements[1].color=(.40,.43,.26,1)
links.new(noise.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs[0],p.inputs['Base Color'])
if level>=2:
    bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=3;links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs[0],p.inputs['Normal'])
verts=[(float(x),float(y),float(h[j,i])) for j,y in enumerate(ys) for i,x in enumerate(xs)];faces=[];nx=len(xs)
for j in range(len(ys)-1):
    for i in range(nx-1):
        a=j*nx+i;faces.extend([(a,a+1,a+nx),(a+1,a+nx+1,a+nx)])
mesh=bpy.data.meshes.new('GSI 25m metric terrain');mesh.from_pydata(verts,[],faces);mesh.update();obj=bpy.data.objects.new('DEM_1to1',mesh);s.collection.objects.link(obj);obj.data.materials.append(terrainmat)
for poly in mesh.polygons:poly.use_smooth=True
stone=mat('Cut edge',(.09,.13,.14))
# Side skirts to z=0, no fake terrain outside DEM.
edge=list(range(nx))+[j*nx+nx-1 for j in range(1,len(ys))]+list(range((len(ys)-1)*nx+nx-2,(len(ys)-1)*nx-1,-1))+[j*nx for j in range(len(ys)-2,0,-1)]
sv=[];sf=[]
for k,idx in enumerate(edge):
    x,y,z=verts[idx];sv.extend([(x,y,z),(x,y,0)])
for k in range(len(edge)):
    a=2*k;b=2*((k+1)%len(edge));sf.append((a,b,b+1,a+1))
me=bpy.data.meshes.new('Terrain skirts');me.from_pydata(sv,[],sf);ob=bpy.data.objects.new('DEM cutaway',me);s.collection.objects.link(ob);ob.data.materials.append(stone)
colors={'west':(.12,.48,.95),'east':(.95,.20,.12),'conditional':(1,.67,.12)};mats={k:mat(k,v,emission=.18) for k,v in colors.items()}
metal=mat('Symbol helmet',(.08,.10,.13));trunk=mat('Procedural trunks',(.17,.11,.07));leaf=mat('Illustrative forest',(.07,.18,.10))
def cube(name,loc,scale,material):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);return o
def line(name,points,material,radius=7):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=radius;cu.bevel_resolution=1;sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
    for p,v in zip(sp.points,points):p.co=(*v,1)
    o=bpy.data.objects.new(name,cu);s.collection.objects.link(o);o.data.materials.append(material);return o
units=json.loads((ROOT/'data'/'units.json').read_text(encoding='utf8'));moving=[];anchors=[]
for u in units:
    x,y=u['x_m'],u['y_m'];m=mats[u['side']]
    pole=cube(u['id']+'_pole',(x,y,height(x,y)+85),(7,7,170),metal)
    flag=cube(u['id']+'_plain_symbolic_flag',(x+47,y,height(x,y)+145),(94,5,50),m)
    anchors.append((u,pole,flag))
    points=[]
    for a in np.linspace(0,2*math.pi,80):
        xx=x+150*math.cos(a);yy=y+150*math.sin(a);points.append((xx,yy,height(xx,yy)+4))
    line('Assumed 150m uncertainty '+u['id'],points,m,2)
    if level>=2:
        for row in range(5):
            for col in range(6):
                # Linked mesh copies of simple armor bodies; feet placed separately on terrain.
                dx=(col-2.5)*28;dy=(row-2)*28;xx=x+dx;yy=y+dy;zz=height(xx,yy)
                body=cube(u['id']+'_soldier',(xx,yy,zz+13),(13,10,26),m)
                bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=9,location=(xx,yy,zz+33));helmet=bpy.context.object;helmet.data.materials.append(metal)
                moving.append((u['id'],dx,dy,body,helmet))
# deterministic procedurally scattered trees on high ground, explicitly illustrative.
if level>=2:
    rng=np.random.default_rng(1600)
    bpy.ops.mesh.primitive_cone_add(vertices=5,radius1=35,depth=100);template=bpy.context.object;template.data.materials.append(leaf);template.hide_render=True
    for i in range(420):
        x=float(rng.uniform(-2900,2900));y=float(rng.uniform(-2900,3400));z=height(x,y)
        if z<220 or any((x-u['x_m'])**2+(y-u['y_m'])**2<260**2 for u in units):continue
        o=bpy.data.objects.new('illustrative_tree',template.data);s.collection.objects.link(o);o.location=(x,y,z+50);o.scale=(1,1,float(rng.uniform(.7,1.4)))
start=next(u for u in units if u['id']=='kobaya');end=next(u for u in units if u['id']=='otani')
route=[]
for a in np.linspace(0,1,100):
    x=start['x_m']*(1-a)+end['x_m']*a;y=start['y_m']*(1-a)+end['y_m']*a;route.append((x,y,height(x,y)+12))
line('HYPOTHETICAL route',route,mats['conditional'],9)
arrow=cube('Moving symbolic arrow',(0,0,0),(65,110,12),mats['conditional'])
bpy.ops.object.light_add(type='SUN',location=(0,0,4000));sun=bpy.context.object;sun.rotation_euler=(.45,-.6,-.6);sun.data.energy=2.5 if level<3 else 3.5;sun.data.angle=.15
if level==3:
    s.eevee.volumetric_start=10;s.eevee.volumetric_end=20000;s.eevee.volumetric_samples=32
    # atmosphere is cinematic, not a factual weather reconstruction
    fog=bpy.data.materials.new('Illustrative cinematic haze');fog.use_nodes=True;n=fog.node_tree.nodes;n.clear();v=n.new('ShaderNodeVolumePrincipled');v.inputs['Density'].default_value=.000065;v.inputs['Color'].default_value=(.52,.64,.74,1);o=n.new('ShaderNodeOutputMaterial');fog.node_tree.links.new(v.outputs['Volume'],o.inputs['Volume'])
    cube('Cinematic haze',(0,0,1300),(18000,18000,3000),fog)
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=9200;cam.data.clip_end=40000;cam.data.clip_start=10
contact=[];metrics=[];N=3 if mode=='bench' else 750
timeline=[]
if mode=='pilot':
    timeline=json.loads((ROOT/'data'/'timeline.json').read_text(encoding='utf8'));N=round(timeline[-1]['end']*30)
for frame in range(N):
    t=frame/max(1,N-1);angle=-math.pi/2+.13*math.sin(t*math.pi*2)
    # Identical path for all levels, cinematic quality affects lighting/haze only.
    cam.location=(7600*math.cos(angle),7600*math.sin(angle),7000);target=Vector((-450,250,160));cam.rotation_euler=(target-Vector(cam.location)).to_track_quat('-Z','Y').to_euler()
    progress=t
    scene_id=None
    if mode=='pilot':
        chapter=next(c for c in timeline if frame/30<c['end']+1e-7);scene_id=chapter['id'];local=(frame/30-chapter['start'])/chapter['duration']
        focus={'ishida':next(u for u in units if u['id']=='ishida'),'ieyasu':next(u for u in units if u['id']=='ieyasu')}
        target=Vector((-450,250,160));cam.data.ortho_scale=9200
        if scene_id==3:target=Vector((focus['ishida']['x_m'],focus['ishida']['y_m']-300,200));cam.data.ortho_scale=4400
        elif scene_id in [4,6,7,8]:target=Vector(((start['x_m']+end['x_m'])/2,(start['y_m']+end['y_m'])/2,190));cam.data.ortho_scale=4300
        elif scene_id==5:target=Vector((200,900,150));cam.data.ortho_scale=6500
        angle=-math.pi/2+.07*math.sin(local*math.pi)
        cam.location=target+Vector((7600*math.cos(angle),7600*math.sin(angle),6800));cam.rotation_euler=(target-Vector(cam.location)).to_track_quat('-Z','Y').to_euler()
        progress=local if scene_id==6 else (0.5 if scene_id in [7,8] else 0)
        arrow.hide_render=scene_id not in [4,6,7,8]
    x=start['x_m']*(1-progress)+end['x_m']*progress;y=start['y_m']*(1-progress)+end['y_m']*progress
    arrow.location=(x,y,height(x,y)+18);arrow.rotation_euler.z=-math.atan2(end['x_m']-start['x_m'],end['y_m']-start['y_m'])
    for u,pole,flag in anchors:
        xx,yy=(x,y) if u['id']=='kobaya' else (u['x_m'],u['y_m'])
        pole.location=(xx,yy,height(xx,yy)+85);flag.location=(xx+47,yy,height(xx,yy)+145)
    for uid,dx,dy,body,helmet in moving:
        u=next(u for u in units if u['id']==uid);xx,yy=(x+dx,y+dy) if uid=='kobaya' else (u['x_m']+dx,u['y_m']+dy)
        zz=height(xx,yy);body.location=(xx,yy,zz+13);helmet.location=(xx,yy,zz+33)
        contact.append(abs(body.location.z-13-height(xx,yy)))
    s.frame_set(frame+1);bpy.context.view_layer.update()
    projections=[]
    for u,pole,flag in anchors:
        v=world_to_camera_view(s,cam,Vector(pole.location)+Vector((0,0,115)))
        projections.append({'id':u['id'],'x':float(v.x),'y':float(1-v.y),'depth':float(v.z)})
    now=time.perf_counter();s.render.filepath=str(out/f'{frame:04}.jpg' if mode=='pilot' else out/f'{frame:04}.png');bpy.ops.render.render(write_still=True)
    metrics.append({'frame':frame,'render_seconds':time.perf_counter()-now,'labels':projections,'camera':list(cam.location),'target':list(target),'chapter':scene_id,'ortho_scale':cam.data.ortho_scale})
    if frame%25==0:
        (out/'progress.json').write_text(json.dumps({'completed':frame+1,'total':N,'mean_s':float(np.mean([m['render_seconds'] for m in metrics]))}),encoding='utf8')
result={'level':level,'mode':mode,'native_resolution':[s.render.resolution_x*s.render.resolution_percentage//100,s.render.resolution_y*s.render.resolution_percentage//100],'frames':metrics,'max_foot_contact_error_m':max(contact,default=0),'total_render_seconds':sum(m['render_seconds'] for m in metrics),'temporal_samples_per_second':30,'camera_path_identical':True,'troop_model_dimensions_m':[13,10,42],'note':'Symbols intentionally oversized; body footprint edges on slopes not verified, center contact checked.'}
(out/'render_report.json').write_text(json.dumps(result,indent=2),encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'scene.blend'))
