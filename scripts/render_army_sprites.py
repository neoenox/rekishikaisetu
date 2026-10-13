"""Render original articulated 3D troop symbols, not historical uniform reconstruction."""
import bpy,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'assets'/'army';out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=16;s.render.resolution_x=320;s.render.resolution_y=256;s.render.resolution_percentage=100;s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.view_settings.view_transform='Standard';s.world.color=(.35,.35,.35)
def mat(name,c):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);return m
metal=mat('dark iron',(.055,.065,.075));wood=mat('wood',(.26,.14,.065));skin=mat('face',(.8,.64,.42));cloth=mat('side color',(.1,.4,.8));trim=mat('light trim',(.77,.73,.59));boots=mat('footwear',(.10,.085,.065))
def cube(name,loc,scale,m,parent=None):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if parent:o.parent=parent
 return o
def sphere(loc,scale,m):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=4,location=loc);o=bpy.context.object;o.scale=scale;o.data.materials.append(m);return o
legs=[];arms=[]
for row in range(4):
 for col in range(5):
  x=(col-2)*15;y=(row-1.5)*22
  cube('cuirass',(x,y,15),(8,6,11),metal);cube('waist sash',(x,y-.3,10),(9,7,3),cloth)
  bpy.ops.mesh.primitive_cone_add(vertices=8,radius1=6,radius2=4,depth=6,location=(x,y,7));bpy.context.object.data.materials.append(cloth)
  sphere((x,y,23),(3.5,3.2,4),skin)
  bpy.ops.mesh.primitive_cone_add(vertices=12,radius1=6,radius2=.8,depth=3,location=(x,y,27));bpy.context.object.data.materials.append(metal)
  for side in [-1,1]:
   pivot=bpy.data.objects.new('hip joint',None);s.collection.objects.link(pivot);pivot.location=(x+side*2.3,y,8)
   cube('leg',(0,0,-3.4),(3,3,6),boots,pivot);cube('foot',(0,-1.2,-6.5),(3.4,5,2.5),boots,pivot);legs.append((pivot,side,row,col))
   pivot=bpy.data.objects.new('shoulder joint',None);s.collection.objects.link(pivot);pivot.location=(x+side*5,y,19)
   cube('sleeve',(0,0,-2.5),(3,4,6),cloth,pivot);cube('forearm',(0,-1,-6.4),(2.4,2.8,4),trim,pivot);arms.append((pivot,side,row,col))
  if col%2==0:
   cube('spear shaft',(x+6,y,20),(1,1,40),wood)
   bpy.ops.mesh.primitive_cone_add(vertices=4,radius1=2,radius2=0,depth=5,location=(x+6,y,42));bpy.context.object.data.materials.append(metal)
  if row==3 and col in [0,2,4]:
   cube('banner pole',(x,y+3,27),(1,1,43),wood);cube('plain identifying banner',(x+4,y+3,42),(9,1,14),cloth)
bpy.ops.object.camera_add(location=(100,-170,280));cam=bpy.context.object;cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=125;s.camera=cam
bpy.ops.object.light_add(type='AREA',location=(-70,-100,180));bpy.context.object.data.energy=150000;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=120
bpy.ops.object.light_add(type='SUN',location=(100,100,200));bpy.context.object.data.energy=2;bpy.context.object.rotation_euler=(.5,-.4,-.6)
for side,color in [('west',(.10,.43,.95)),('east',(.95,.20,.13)),('kobaya',(.95,.65,.15))]:
 cloth.diffuse_color=(*color,1)
 for frame in range(12):
  for joint,sign,row,col in legs:joint.rotation_euler.x=sign*.32*math.sin(frame/12*2*math.pi+row*.7+col*.3)
  for joint,sign,row,col in arms:joint.rotation_euler.x=-sign*.22*math.sin(frame/12*2*math.pi+row*.7+col*.3)
  s.render.filepath=str(out/f'{side}_{frame:02}.png');bpy.ops.render.render(write_still=True)
print('36 3D troop-symbol sprites rendered')
