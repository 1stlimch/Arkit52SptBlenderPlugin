bl_info = {
    "name": "limch ARKit ShapeKeys Generator",
    "author": "Limch",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > ARKit Keys",
    "description": "AR52를 셰이프키 작업 보조.",
    "category": "Mesh",
}

import bpy
from mathutils import kdtree

# X미러 키고 양쪽으로 작업, 양쪽으로 분리될 키, 11/22개
SKEY_NAMES = [
    'S_browDown',
    'S_browOuterUp',
    'S_eyeLookUp', 
    'S_eyeLookDown',
    'S_eyeBlink',
    'S_eyeSquint',
    'S_eyeWide',
    'S_cheekSquint',
    'S_noseSneer',
    'S_mouthFrown',
    'S_mouthDimple'
]

# 한쪽방향으로 작업하고, 좌우반전될키, 7/14개
MKEY_NAMES = [
    'M_jawLeft',
    'M_mouthLeft',
    'M_mouthSmileLeft',
    'M_mouthUpperUpLeft',
    'M_mouthLowerDownLeft',
    'M_mouthPressLeft',
    'M_mouthStretchLeft'
]

# 중앙부 변형이라 좌우가 없거나, 좌우반전하면 안되는 키 16개, 
BKEY_NAMES = [
    'B_browInnerUp',
    'B_eyeLookInLeft',
    'B_eyeLookInRight',
    'B_eyeLookOutLeft',
    'B_eyeLookOutRight',
    'B_cheekPuff',
    'B_jawOpen',
    'B_jawForward',
    'B_mouthFunnel',
    'B_mouthPucker',
    'B_mouthRollUpper',
    'B_mouthRollLower',
    'B_mouthShrugUpper', 
    'B_mouthShrugLower', 
    'B_mouthClose',
    'B_tongueOut'
]

ARKit52_NAMES = [
    # Eyes
    "eyeBlinkLeft",
    "eyeBlinkRight",
    "eyeLookDownLeft",
    "eyeLookDownRight",
    "eyeLookInLeft",
    "eyeLookInRight",
    "eyeLookOutLeft",
    "eyeLookOutRight",
    "eyeLookUpLeft",
    "eyeLookUpRight",
    "eyeSquintLeft",
    "eyeSquintRight",
    "eyeWideLeft",
    "eyeWideRight",

    # Jaw
    "jawForward",
    "jawLeft",
    "jawRight",
    "jawOpen",

    # Mouth
    "mouthClose",
    "mouthFunnel",
    "mouthPucker",
    "mouthLeft",
    "mouthRight",
    "mouthSmileLeft",
    "mouthSmileRight",
    "mouthFrownLeft",
    "mouthFrownRight",
    "mouthDimpleLeft",
    "mouthDimpleRight",
    "mouthStretchLeft",
    "mouthStretchRight",
    "mouthRollLower",
    "mouthRollUpper",
    "mouthShrugLower",
    "mouthShrugUpper",
    "mouthPressLeft",
    "mouthPressRight",
    "mouthLowerDownLeft",
    "mouthLowerDownRight",
    "mouthUpperUpLeft",
    "mouthUpperUpRight",

    # Brow
    "browDownLeft",
    "browDownRight",
    "browInnerUp",
    "browOuterUpLeft",
    "browOuterUpRight",

    # Cheek
    "cheekPuff",
    "cheekSquintLeft",
    "cheekSquintRight",

    # Nose
    "noseSneerLeft",
    "noseSneerRight",

    # Tongue
    "tongueOut",
]

# 좌우 분리 함수
def splitKey(obj, source_key_name: str) : 
    key_blocks = obj.data.shape_keys.key_blocks

    if source_key_name in key_blocks:
        # 원본 셰이프 키 선택
        obj.active_shape_key_index = key_blocks.find(source_key_name)
        source_key = key_blocks[source_key_name]
        
        # 셰이프 키 복사 (New Shape From Mix)
        new_key_left = obj.shape_key_add(name=f"{source_key_name[2:]}Left", from_mix=False)
        new_key_right = obj.shape_key_add(name=f"{source_key_name[2:]}Right", from_mix=False)
        
        # 2. left
        for i, vert in enumerate(source_key.data):
            # 원본 좌표 가져오기
            co = vert.co.copy()
            if co.x >= 0 :
                new_key_left.data[i].co = (co.x, co.y, co.z)
            
        # 3. right
        for i, vert in enumerate(source_key.data):
            # 원본 좌표 가져오기
            co = vert.co.copy()
            if co.x <= 0 :
                new_key_right.data[i].co = (co.x, co.y, co.z)

        source_key.value = 0
    return

# 좌우 대칭 함수
def mirrorKey(obj, source_key_name: str) : 
    key_blocks = obj.data.shape_keys.key_blocks

    # 이름
    name_l = source_key_name[2:]
    name_r = f"{source_key_name[2:-4]}Right"

    # 기존 키가 있으면 삭제
    if name_l in key_blocks:
        obj.shape_key_clear()
        obj.active_shape_key_index = key_blocks.find(name_l)
        obj.shape_key_remove(key_blocks[name_l])

    if name_r in key_blocks:
        obj.shape_key_clear()
        obj.active_shape_key_index = key_blocks.find(name_r)
        obj.shape_key_remove(key_blocks[name_r])

    # Shape Key 생성
    key_l = obj.shape_key_add(name=name_l, from_mix=False)
    key_r = obj.shape_key_add(name=name_r, from_mix=False)

    source = key_blocks[source_key_name]
    basis = key_blocks["Basis"]

    # --------------------------------------------------
    # 1. Source → Left Key 복사
    # --------------------------------------------------

    for i in range(len(source.data)):
        key_l.data[i].co = source.data[i].co

    # --------------------------------------------------
    # 2. Basis의 좌우 대응 Vertex 찾기
    # --------------------------------------------------

    kd = kdtree.KDTree(len(basis.data))

    for i, vert in enumerate(basis.data):
        kd.insert(vert.co, i)

    kd.balance()

    mirror_map = {}

    for i, vert in enumerate(basis.data):

        # 현재 Vertex의 X축 미러 위치
        mirror_co = vert.co.copy()
        mirror_co.x *= -1

        # 가장 가까운 Vertex 검색
        _, index, distance = kd.find(mirror_co)

        mirror_map[i] = index

    # --------------------------------------------------
    # 3. Left → Right Mirror
    # --------------------------------------------------

    for i in range(len(key_l.data)):

        # Basis → Left Shape Key 변위
        delta = key_l.data[i].co - basis.data[i].co

        # X축 변위 반전
        delta.x *= -1

        # 대응되는 반대쪽 Vertex
        mirror_index = mirror_map[i]

        # Basis + 반전된 변위
        key_r.data[mirror_index].co = (
            basis.data[mirror_index].co + delta
        )

    # --------------------------------------------------
    # 4. 원본 작업용 Key 비활성화
    # --------------------------------------------------

    source.value = 0
    return

# 1. 작업용 키등록
class MESH_OT_add_arkit_shapekeys(bpy.types.Operator):
    """선택한 메시에 ARKit 작업용 키를 추가합니다"""
    bl_idname = "mesh.add_arkit_shapekeys"
    bl_label = "ARKit 작업용 생성"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "메시 오브젝트를 선택해 주세요.")
            return {'CANCELLED'}

        # Basis 생성
        if not obj.data.shape_keys:
            obj.shape_key_add(name="Basis", from_mix=False)

        count = 0
        existing_keys = obj.data.shape_keys.key_blocks        

        for sname in SKEY_NAMES:
            if sname not in existing_keys:
                new_key = obj.shape_key_add(name=sname, from_mix=False)
                new_key.value = 1
                count += 1

        for sname in MKEY_NAMES:
            if sname not in existing_keys:
                new_key = obj.shape_key_add(name=sname, from_mix=False)
                new_key.value = 1
                count += 1

        for sname in BKEY_NAMES:
            if sname not in existing_keys:
                new_key = obj.shape_key_add(name=sname, from_mix=False)
                new_key.value = 1
                count += 1

        self.report({'INFO'}, f"총 {count}개의 셰이프키가 추가되었습니다.")
        return {'FINISHED'}


# 2. S키 좌우 분리
class MESH_OT_split_SKEY(bpy.types.Operator):
    """S키 전체를 좌우 분리하여 새로운 실제 키를 생성합니다. S키 영향력이 0으로 변경됩니다. 실제키가 없어야 정상작동합니다."""
    bl_idname = "mesh.split_s_shapekeys"
    bl_label = "S키 좌우 분리"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "메시 오브젝트를 선택해 주세요.")
            return {'CANCELLED'}

        for sname in SKEY_NAMES :
            splitKey(obj, sname)

        self.report({'INFO'}, "S키가 좌우 분리되었습니다.")
        return {'FINISHED'}
    

# 3. M키 좌우 반전
class MESH_OT_Mirror_MKEY(bpy.types.Operator):
    """M키 전체를 좌우 반전하여 새로운 실제 키를 생성합니다. M키 영향력이 0으로 변경됩니다. 실제키가 없어야 정상작동합니다."""
    bl_idname = "mesh.mirror_m_shapekeys"
    bl_label = "M키 좌우 반전"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "메시 오브젝트를 선택해 주세요.")
            return {'CANCELLED'}

        for sname in MKEY_NAMES :
            mirrorKey(obj, sname)

        self.report({'INFO'}, "M키가 좌우 대칭되었습니다.")
        return {'FINISHED'}

    
# 4. B키 네이밍 변경
class MESH_OT_Copy_BKEY(bpy.types.Operator):
    """B키 전체를 복사 생성후 이름만 실제키로 변경합니다., 실제키가 없어야 정상작동합니다."""
    bl_idname = "mesh.copy_b_shapekeys"
    bl_label = "B키 복사&이름변경"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context): 
        obj = context.active_object

        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "메시 오브젝트를 선택해 주세요.")
            return {'CANCELLED'}

        for sname in BKEY_NAMES :
            newName = sname[2:]
            obj.shape_key_add(name=newName, from_mix=False)

            source_key = obj.data.shape_keys.key_blocks[sname]
            new_key = obj.data.shape_keys.key_blocks[newName]
            for i, vert in enumerate(source_key.data):
                co = vert.co.copy()
                new_key.data[i].co = (co.x, co.y, co.z)

            source_key.value = 0

        self.report({'INFO'}, "B키의 이름이 변경되었습니다.")
        return {'FINISHED'}

# 5. 작업키 삭제
class MESH_OT_Del_WORK_KEY(bpy.types.Operator):
    """작업키 전부를 삭제합니다."""
    bl_idname = "mesh.del_work_shapekeys"
    bl_label = "작업키 삭제"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context): 
        obj = context.active_object
        key_blocks = obj.data.shape_keys.key_blocks
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "메시 오브젝트를 선택해 주세요.")
            return {'CANCELLED'}

        for sname in SKEY_NAMES :
            if sname in key_blocks:
                obj.active_shape_key_index = key_blocks.find(sname)
                obj.shape_key_remove(key_blocks[sname])

        for sname in MKEY_NAMES :
            if sname in key_blocks:
                obj.active_shape_key_index = key_blocks.find(sname)
                obj.shape_key_remove(key_blocks[sname])

        for sname in BKEY_NAMES :
            if sname in key_blocks:
                obj.active_shape_key_index = key_blocks.find(sname)
                obj.shape_key_remove(key_blocks[sname])
            

        self.report({'INFO'}, "모든 작업키가 삭제되었습니다.")
        return {'FINISHED'}


# 6. 실제키 삭제
class MESH_OT_Del_REAL_KEY(bpy.types.Operator):
    """실제키 전부를 삭제합니다."""
    bl_idname = "mesh.del_real_shapekeys"
    bl_label = "실제키 삭제"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context): 
        obj = context.active_object
        key_blocks = obj.data.shape_keys.key_blocks
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "메시 오브젝트를 선택해 주세요.")
            return {'CANCELLED'}

        for sname in ARKit52_NAMES :
            if sname in key_blocks:
                obj.active_shape_key_index = key_blocks.find(sname)
                obj.shape_key_remove(key_blocks[sname])
            

        self.report({'INFO'}, "모든 실제키가 삭제되었습니다.")
        return {'FINISHED'}


# UI 패널 (Panel)
class VIEW3D_PT_arkit_shapekeys_panel(bpy.types.Panel):
    bl_label = "ARKit ShapeKey Support"
    bl_idname = "VIEW3D_PT_arkit_shapekeys_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "limch ARKit"  # N 패널의 탭 이름

    def draw(self, context):
        layout = self.layout

        layout.operator(
            "mesh.add_arkit_shapekeys",
            icon='SHAPEKEY_DATA'
        )

        layout.operator(
            "mesh.split_s_shapekeys",
            icon='MOD_MIRROR'
        )

        layout.operator(
            "mesh.mirror_m_shapekeys",
            icon='MOD_MIRROR'
        )

        layout.operator(
            "mesh.copy_b_shapekeys",
            icon='SHAPEKEY_DATA'
        )

        layout.operator(
            "mesh.del_work_shapekeys",
            icon='SHAPEKEY_DATA'
        )

        layout.operator(
            "mesh.del_real_shapekeys",
            icon='SHAPEKEY_DATA'
        )

# 클래스 등록/해제
classes = (
    MESH_OT_add_arkit_shapekeys,
    MESH_OT_split_SKEY,
    MESH_OT_Mirror_MKEY,
    MESH_OT_Copy_BKEY,
    MESH_OT_Del_WORK_KEY,
    MESH_OT_Del_REAL_KEY,
    VIEW3D_PT_arkit_shapekeys_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()