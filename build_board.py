"""Generate editable KiCad 9 XT30 distribution board and matching schematic."""
from pathlib import Path
import json, math, re, uuid
import pcbnew as p
import wx
app = wx.App(False)

ROOT = Path(__file__).resolve().parent
LIB = Path(r'C:\Program Files\KiCad\9.0\share\kicad')
NAME = 'xt30-distribution'
uid = lambda text: str(uuid.uuid5(uuid.NAMESPACE_URL, 'xt30-distribution/' + text))
mm = p.FromMM
vec = lambda x,y: p.VECTOR2I(mm(x),mm(y))
board = p.BOARD()
title=p.TITLE_BLOCK()
title.SetTitle('VSReality Robotics - PD-XT30-5')
title.SetRevision('1.0')
board.SetTitleBlock(title)
board.SetCopperLayerCount(2)
ds = board.GetDesignSettings()
ds.SetBoardThickness(mm(1.6))
ds.m_MinClearance = mm(0.5)
ds.m_CopperEdgeClearance = mm(0.5)
ds.m_SolderMaskExpansion = mm(0.05)
ds.m_SolderMaskMinWidth = mm(0.1)
nets = {}
for name in ['GND','V+']:
    net = p.NETINFO_ITEM(board,'/'+name)
    board.Add(net)
    nets[name] = net

def line(a,b,layer=p.Edge_Cuts,width=0.05):
    s=p.PCB_SHAPE(); s.SetShape(p.SHAPE_T_SEGMENT)
    s.SetStart(vec(*a)); s.SetEnd(vec(*b)); s.SetLayer(layer); s.SetWidth(mm(width)); board.Add(s)

def text(t,x,y,size=1.0,layer=p.F_SilkS,angle=0):
    s=p.PCB_TEXT(board); s.SetText(t); s.SetPosition(vec(x,y)); s.SetTextSize(vec(size,size))
    s.SetTextThickness(mm(0.15)); s.SetLayer(layer)
    s.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T))
    if layer==p.B_SilkS: s.SetMirrored(True)
    board.Add(s)

# 18 x 52 mm board, 4 mm corner radii. Side labels and 7 mm connector pitch.
outline=[]
for cx,cy,start in [(64,54,-90),(64,98,0),(54,98,90),(54,54,180)]:
    for j in range(17):
        a=math.radians(start+j*90/16)
        outline.append((cx+4*math.cos(a),cy+4*math.sin(a)))
for a,b in zip(outline,outline[1:]+outline[:1]): line(a,b)

ports=[('J1','1',59,62,'F'),('J2','2',59,69,'M'),('J3','3',59,76,'M'),
       ('J4','4',59,83,'M'),('J5','5',59,90,'M')]
footprints={}
for ref,label,cx,cy,sex in ports:
    name=f'AMASS_XT30UPB-{sex}_1x02_P5.0mm_Vertical'
    fp=p.FootprintLoad(str(LIB/'footprints/Connector_AMASS.pretty'),name)
    fp.SetFPID(p.LIB_ID('Connector_AMASS',name)); fp.SetReference(ref); fp.SetValue(f'XT30UPB-{sex}')
    fp.SetOrientationDegrees(180)
    fp.SetPosition(vec(cx+2.5,cy)); fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
    # Replace footprint polarity text with visible board-level markings.
    for graphic in list(fp.GraphicalItems()):
        if isinstance(graphic,p.PCB_TEXT) and graphic.GetText() in ['+','-']:
            fp.Remove(graphic)
    path=p.KIID_PATH(); path.push_back(p.KIID(uid('root'))); path.push_back(p.KIID(uid(ref))); fp.SetPath(path)
    for pad in fp.Pads():
        pad.SetNet(nets['GND' if pad.GetNumber()=='1' else 'V+'])
        pad.SetLocalZoneConnection(p.ZONE_CONNECTION_FULL)
    board.Add(fp); footprints[ref]=f'Connector_AMASS:{name}'
    text(label,66,cy,1.1)

text('+',56.5,58.2,1.1)
text('-',61.5,58.2,1.1)

holes=[(59,55),(59,97)]
for i,(x,y) in enumerate(holes,1):
    fp=p.FootprintLoad(str(LIB/'footprints/MountingHole.pretty'),'MountingHole_3.2mm_M3')
    fp.SetFPID(p.LIB_ID('MountingHole','MountingHole_3.2mm_M3')); fp.SetReference(f'H{i}')
    fp.SetValue('M3 / 3.2mm'); fp.SetPosition(vec(x,y)); fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
    fp.SetBoardOnly(True); board.Add(fp)
    # 7 mm diameter keepout accommodates 6 mm OD washers plus 0.5 mm margin.
    z=p.ZONE(board); z.SetIsRuleArea(True); z.SetLayerSet(p.LSET.AllCuMask())
    z.SetDoNotAllowCopperPour(True); z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    poly=z.Outline(); poly.NewOutline()
    for j in range(64):
        a=2*math.pi*j/64; poly.Append(mm(x+3.5*math.cos(a)),mm(y+3.5*math.sin(a)))
    board.Add(z)

for name,layer in [('V+',p.F_Cu),('GND',p.F_Cu),('V+',p.B_Cu),('GND',p.B_Cu)]:
    z=p.ZONE(board); z.SetNet(nets[name]); z.SetLayer(layer)
    z.SetZoneName('V+ LEFT RAIL' if name=='V+' else 'GND REMAINING AREA')
    z.SetAssignedPriority(1 if name=='V+' else 0)
    z.SetLocalClearance(mm(0.5)); z.SetMinThickness(mm(0.25)); z.SetPadConnection(p.ZONE_CONNECTION_FULL)
    z.SetThermalReliefGap(mm(0.5)); z.SetThermalReliefSpokeWidth(mm(1.0))
    poly=z.Outline(); poly.NewOutline()
    # V+ avoids the mounting regions. GND fills everything else except
    # clearances, board edges and the existing screw/washer keepouts.
    # Higher-priority V+ reserves its strip with a 0.5 mm gap to GND.
    zone_outline=[(50,60),(58.75,60),(58.75,92),(50,92)] if name=='V+' else outline
    for x,y in zone_outline: poly.Append(mm(x),mm(y))
    board.Add(z)

for ref,label,cx,cy,sex in ports:
    text(label,66,cy,1.1,p.B_SilkS)
    text('+',cx-2.5,cy-2.6,1.1,p.B_SilkS); text('-',cx+2.5,cy-2.6,1.1,p.B_SilkS)

for layer in [p.B_SilkS]:
    text('PD-XT30-5',59,51.7,0.9,layer)
    text('VSReality Robotics',51.8,76,0.9,layer,90)
    text('v1.0',59,100.4,1.0,layer)

path=ROOT/(NAME+'.kicad_pcb')
p.SaveBoard(str(path),board)
board=p.LoadBoard(str(path))
board.BuildConnectivity()
filler=p.ZONE_FILLER(board)
filler.Fill(board.Zones())
p.SaveBoard(str(path),board)
pcb=path.read_text()
stack='''(stackup
      (layer "F.SilkS" (type "Top Silk Screen"))
      (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
      (layer "F.Cu" (type "copper") (thickness 0.07))
      (layer "dielectric 1" (type "core") (thickness 1.44) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
      (layer "B.Cu" (type "copper") (thickness 0.07))
      (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
      (layer "B.SilkS" (type "Bottom Silk Screen"))
      (copper_finish "HASL lead-free") (dielectric_constraints no))'''
pcb=pcb.replace('(setup','(setup\n    '+stack,1)
# Connector models are centred between pins; library footprint origin is pin 1.
for sex in ['F','M']:
    old=f'(model "${{KICAD9_3DMODEL_DIR}}/Connector_AMASS.3dshapes/AMASS_XT30UPB-{sex}_1x02_P5.0mm_Vertical.step"'
    pattern=re.escape(old)+r'\s*\(offset\s*\(xyz 0 0 0\)'
    new=f'(model "${{KIPRJMOD}}/models/Amass_XT30UPB-{sex}.step" (offset (xyz 2.5 0 0)'
    pcb=re.sub(pattern,lambda m:new,pcb)
path.write_text(pcb)

project={'meta':{'filename':NAME+'.kicad_pro','version':1},
 'board':{'design_settings':{'rules':{'min_clearance':0.5,'min_copper_edge_clearance':0.5,
 'min_hole_clearance':0.25,'min_silk_clearance':0.15,'min_track_width':0.25},
 'defaults':{'board_outline_line_width':0.05,'copper_line_width':0.25}}},
 'net_settings':{'classes':[{'name':'Default','clearance':0.5,'track_width':2.0,
 'via_diameter':0.8,'via_drill':0.4,'microvia_diameter':0.3,'microvia_drill':0.1,
 'diff_pair_width':0.25,'diff_pair_gap':0.2,'diff_pair_via_gap':0.25}]}}
(ROOT/(NAME+'.kicad_pro')).write_text(json.dumps(project,indent=2))
(ROOT/'fp-lib-table').write_text(f'(fp_lib_table (version 7) (lib (name "Connector_AMASS") (type "KiCad") (uri "${{KICAD9_FOOTPRINT_DIR}}/Connector_AMASS.pretty") (options "") (descr "")) (lib (name "MountingHole") (type "KiCad") (uri "${{KICAD9_FOOTPRINT_DIR}}/MountingHole.pretty") (options "") (descr "")))')

def extract_sexp(src,needle):
    start=src.index(needle); depth=0; quoted=False; escaped=False
    for end in range(start,len(src)):
        c=src[end]
        if quoted:
            if escaped: escaped=False
            elif c=='\\': escaped=True
            elif c=='"': quoted=False
        elif c=='"': quoted=True
        elif c=='(': depth+=1
        elif c==')':
            depth-=1
            if depth==0: return src[start:end+1]

symbol=extract_sexp((LIB/'symbols/Connector_Generic.kicad_sym').read_text(),'(symbol "Conn_01x02"')
symbol=symbol.replace('(symbol "Conn_01x02"','(symbol "Connector_Generic:Conn_01x02"',1)
sch=[f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {uid("root")}) (paper "A4")',
 '(title_block (title "VSReality Robotics - PD-XT30-5") (rev "1.0"))',
 f'(lib_symbols {symbol})']
def schtext(t,x,y,size=1.27):
    sch.append(f'(text "{t}" (at {x} {y} 0) (effects (font (size {size} {size})) (justify left)) (uuid {uid(t)}))')
schtext('VSReality Robotics - PD-XT30-5 v1.0',30,30,2.5)
schtext('Passive parallel bus: each output receives the input voltage.',30,40)
schtext('Pin 1 = GND (-). Pin 2 = V+ (+). No fuses, regulation or reverse-polarity protection.',30,47)
for i,(ref,label,cx,cy,sex) in enumerate(ports):
    x=50.8+i*44.45; y=81.28
    sch.append(f'''(symbol (lib_id "Connector_Generic:Conn_01x02") (at {x} {y} 0) (unit 1)
      (in_bom yes) (on_board yes) (dnp no) (uuid {uid(ref)})
      (property "Reference" "{ref}" (at {x+3} {y-5} 0) (effects (font (size 1.27 1.27))))
      (property "Value" "XT30UPB-{sex}" (at {x+4} {y+7} 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "{footprints[ref]}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (pin "1" (uuid {uid(ref+'1')})) (pin "2" (uuid {uid(ref+'2')}))
      (instances (project "{NAME}" (path "/{uid('root')}" (reference "{ref}") (unit 1)))))''')
    schtext(label,x-7,y-12)
    for n,net in [(1,'GND'),(2,'V+')]:
        py=y+(n-1)*2.54
        sch.append(f'(wire (pts (xy {x-5.08} {py}) (xy {x-12.7} {py})) (stroke (width 0) (type default)) (uuid {uid(ref+net+"wire")}))')
        sch.append(f'(label "{net}" (at {x-12.7} {py} 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid {uid(ref+net+"label")}))')
schtext('PCB: 18 x 52 mm, 1.6 mm FR4, 2 layers, 70 um (2 oz) copper per layer.',30,110)
schtext('Two 3.2 mm NPTH mounting holes for M3 screws; mounting centres 42 mm.',30,117)
schtext('7 mm diameter copper keepouts at mounting holes. Solid pad-to-plane connections.',30,124)
schtext('Both layers: V+ left strip, GND fills remaining area. M3 screw keepouts remain copper-free.',30,131)
schtext('PROVISIONAL: connector gender, operating voltage and total continuous current require confirmation.',30,143)
schtext('The input connector carries the SUM of all output currents. Thermal load test required.',30,150)
sch.append('(embedded_fonts no))')
(ROOT/(NAME+'.kicad_sch')).write_text('\n'.join(sch))
print('Generated PCB, project and schematic:', ROOT)
import os, sys
sys.stdout.flush()
os._exit(0)



